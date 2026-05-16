FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt infra/streamlit/requirements.txt ./infra/streamlit/
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY repoquest ./repoquest
COPY examples ./examples
COPY docs ./docs
COPY infra ./infra
COPY scripts ./scripts
COPY .streamlit ./.streamlit
COPY README.md pyproject.toml ./

EXPOSE 8501

CMD ["python", "scripts/run_local.py"]
