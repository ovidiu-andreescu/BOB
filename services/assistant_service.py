"""Asynchronous assistant service for optional RepoQuest AI mode.

This service keeps model/provider calls out of the Streamlit process. It accepts
bounded RepoQuest assistant requests, queues them in memory, and exposes job
status over a tiny standard-library HTTP API.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from repoquest.assistant_models import AssistantRequest, AssistantResponse
from repoquest.assistant_provider import (
  ClaudeAssistantProvider,
  DisabledAssistantProvider,
  LocalModelAssistantProvider,
  MockAssistantProvider,
  get_assistant_config,
)


MAX_REQUEST_BYTES = 256_000
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8765
DEFAULT_WORKERS = 2


@dataclass
class AssistantJob:
  """In-memory assistant job state."""

  job_id: str
  status: str
  response: AssistantResponse | None = None
  message: str | None = None

  def to_dict(self) -> dict[str, Any]:
    """Return JSON-serializable job state."""
    return {
      "job_id": self.job_id,
      "status": self.status,
      "response": self.response.to_dict() if self.response else None,
      "message": self.message,
    }


class AssistantJobStore:
  """Thread-safe in-memory assistant job store."""

  def __init__(self):
    self._jobs: dict[str, AssistantJob] = {}
    self._lock = threading.Lock()

  def create(self) -> AssistantJob:
    """Create a queued job."""
    job = AssistantJob(job_id=uuid.uuid4().hex, status="queued")
    with self._lock:
      self._jobs[job.job_id] = job
    return job

  def get(self, job_id: str) -> AssistantJob | None:
    """Return a job by id."""
    with self._lock:
      return self._jobs.get(job_id)

  def update(
    self,
    job_id: str,
    status: str,
    response: AssistantResponse | None = None,
    message: str | None = None,
  ) -> None:
    """Update job state."""
    with self._lock:
      job = self._jobs.get(job_id)
      if job is None:
        return
      job.status = status
      job.response = response
      job.message = message


def build_service_provider():
  """Build the provider used inside the assistant service."""
  provider_name = os.getenv("REPOQUEST_ASSISTANT_SERVICE_PROVIDER", "").strip().lower()
  ai_enabled, provider, api_key, model, local_base_url, local_model_name = get_assistant_config()
  if not provider_name:
    provider_name = provider

  if provider_name == "mock":
    return MockAssistantProvider(
      mock_response=(
        "Mock assistant service response. Review the deterministic RepoQuest evidence "
        "before making code changes."
      )
    )

  if not ai_enabled:
    return DisabledAssistantProvider()

  if provider_name == "local":
    if not local_base_url or not local_model_name:
      return DisabledAssistantProvider()
    return LocalModelAssistantProvider(base_url=local_base_url, model=local_model_name)

  if not api_key:
    return DisabledAssistantProvider()

  return ClaudeAssistantProvider(api_key=api_key, model=model)


STORE = AssistantJobStore()
EXECUTOR = ThreadPoolExecutor(max_workers=DEFAULT_WORKERS)


def run_job(job_id: str, request: AssistantRequest) -> None:
  """Execute one assistant request in a worker thread."""
  STORE.update(job_id, "running")

  try:
    provider = build_service_provider()
    response = provider.generate(request)
    status = response.status if response.status in {"ok", "error", "invalid"} else "error"
    STORE.update(job_id, status, response=response, message=response.message)
  except Exception as exc:
    STORE.update(
      job_id,
      "error",
      response=AssistantResponse(
        status="error",
        response_text="",
        provider="assistant-service",
        model="remote",
        message=f"Assistant service worker error: {exc}",
      ),
      message=str(exc),
    )


class AssistantServiceHandler(BaseHTTPRequestHandler):
  """HTTP handler for assistant jobs."""

  server_version = "RepoQuestAssistantService/1.0"

  def do_GET(self) -> None:
    """Handle health checks and job polling."""
    parsed = urlparse(self.path)

    if parsed.path == "/health":
      self._send_json({"status": "ok"})
      return

    if parsed.path.startswith("/jobs/"):
      job_id = parsed.path.removeprefix("/jobs/").strip("/")
      job = STORE.get(job_id)
      if job is None:
        self._send_json({"message": "job not found"}, status=HTTPStatus.NOT_FOUND)
        return
      self._send_json(job.to_dict())
      return

    self._send_json({"message": "not found"}, status=HTTPStatus.NOT_FOUND)

  def do_POST(self) -> None:
    """Handle assistant job creation."""
    parsed = urlparse(self.path)
    if parsed.path != "/jobs":
      self._send_json({"message": "not found"}, status=HTTPStatus.NOT_FOUND)
      return

    content_length = int(self.headers.get("Content-Length", "0") or "0")
    if content_length <= 0:
      self._send_json({"message": "missing request body"}, status=HTTPStatus.BAD_REQUEST)
      return
    if content_length > MAX_REQUEST_BYTES:
      self._send_json(
        {"message": "request body too large"},
        status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
      )
      return

    try:
      payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
      request_payload = payload.get("request") if isinstance(payload, dict) else None
      if not isinstance(request_payload, dict):
        raise ValueError("payload must include a request object")
      request = AssistantRequest.from_dict(request_payload)
    except (json.JSONDecodeError, ValueError) as exc:
      self._send_json({"message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
      return

    job = STORE.create()
    EXECUTOR.submit(run_job, job.job_id, request)
    self._send_json({"job_id": job.job_id, "status": job.status}, status=HTTPStatus.ACCEPTED)

  def log_message(self, format: str, *args) -> None:
    """Keep service logs short and predictable."""
    print(f"{self.address_string()} - {format % args}")

  def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
    """Write a JSON response."""
    body = json.dumps(payload).encode("utf-8")
    self.send_response(status.value)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)


def main() -> None:
  """Run the assistant HTTP service."""
  parser = argparse.ArgumentParser(description="Run the RepoQuest assistant service")
  parser.add_argument("--host", default=os.getenv("REPOQUEST_ASSISTANT_SERVICE_HOST", DEFAULT_HOST))
  parser.add_argument(
    "--port",
    type=int,
    default=int(os.getenv("REPOQUEST_ASSISTANT_SERVICE_PORT", str(DEFAULT_PORT))),
  )
  args = parser.parse_args()

  server = ThreadingHTTPServer((args.host, args.port), AssistantServiceHandler)
  print(f"RepoQuest assistant service listening on http://{args.host}:{args.port}")
  server.serve_forever()


if __name__ == "__main__":
  main()
