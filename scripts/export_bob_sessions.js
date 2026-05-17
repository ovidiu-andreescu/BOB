#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const [sourceRoot = path.join(process.env.HOME, ".bob", "tmp"), outputRoot = path.resolve("bob-exports")] =
  process.argv.slice(2);

function walk(dir, files = []) {
  if (!fs.existsSync(dir)) {
    return files;
  }

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const filePath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(filePath, files);
    } else if (entry.isFile() && entry.name.endsWith(".json") && filePath.includes(`${path.sep}chats${path.sep}`)) {
      files.push(filePath);
    }
  }

  return files;
}

function safeName(value) {
  return String(value || "unknown")
    .replace(/[:.]/g, "-")
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function headingFromMessage(session) {
  const firstUser = (session.messages || []).find((message) => message.type === "user" && message.content.trim());
  if (!firstUser) {
    return "Empty conversation";
  }

  const firstLine = firstUser.content.split(/\r?\n/).find((line) => line.trim()) || firstUser.content;
  return firstLine.trim().slice(0, 120);
}

function tableCell(value) {
  return String(value || "")
    .replace(/\r?\n/g, " ")
    .replace(/`/g, "")
    .replace(/\|/g, "\\|")
    .trim();
}

function formatMessage(message) {
  const role = message.type === "bob-shell" ? "Bob Shell" : message.type;
  const lines = [`## ${role}`, "", `Timestamp: ${message.timestamp || "unknown"}`, ""];

  if (message.model) {
    lines.push(`Model: ${message.model}`, "");
  }

  if (message.content && message.content.trim()) {
    lines.push(message.content.trim(), "");
  } else {
    lines.push("_No text content._", "");
  }

  if (Array.isArray(message.toolCalls) && message.toolCalls.length > 0) {
    lines.push("<details>", "<summary>Tool calls</summary>", "", "```json");
    lines.push(JSON.stringify(message.toolCalls, null, 2));
    lines.push("```", "", "</details>", "");
  }

  if (Array.isArray(message.thoughts) && message.thoughts.length > 0) {
    lines.push("<details>", "<summary>Thoughts metadata</summary>", "", "```json");
    lines.push(JSON.stringify(message.thoughts, null, 2));
    lines.push("```", "", "</details>", "");
  }

  return lines.join("\n");
}

function exportSession(filePath, markdownDir, rawDir) {
  const session = JSON.parse(fs.readFileSync(filePath, "utf8"));
  const title = headingFromMessage(session);
  const start = session.startTime || "unknown-start";
  const id = session.sessionId || path.basename(filePath, ".json");
  const baseName = `${safeName(start)}_${safeName(id.slice(0, 8))}`;
  const markdownPath = path.join(markdownDir, `${baseName}.md`);
  const rawPath = path.join(rawDir, `${baseName}.json`);

  const body = [
    `# ${title}`,
    "",
    `Session ID: ${session.sessionId || "unknown"}`,
    `Project hash: ${session.projectHash || "unknown"}`,
    `Start time: ${session.startTime || "unknown"}`,
    `Last updated: ${session.lastUpdated || "unknown"}`,
    `Source file: ${filePath}`,
    `Message count: ${(session.messages || []).length}`,
    "",
    "---",
    "",
    ...(session.messages || []).map(formatMessage),
  ].join("\n");

  fs.writeFileSync(markdownPath, body);
  fs.copyFileSync(filePath, rawPath);

  return {
    title,
    sessionId: session.sessionId || "",
    projectHash: session.projectHash || "",
    startTime: session.startTime || "",
    lastUpdated: session.lastUpdated || "",
    messageCount: (session.messages || []).length,
    markdownPath,
    rawPath,
    sourcePath: filePath,
  };
}

fs.mkdirSync(outputRoot, { recursive: true });
const markdownDir = path.join(outputRoot, "markdown");
const rawDir = path.join(outputRoot, "raw-json");
fs.mkdirSync(markdownDir, { recursive: true });
fs.mkdirSync(rawDir, { recursive: true });

const sessions = walk(sourceRoot)
  .map((filePath) => exportSession(filePath, markdownDir, rawDir))
  .sort((a, b) => a.startTime.localeCompare(b.startTime));

const indexLines = [
  "# IBM Bob Conversation Export",
  "",
  `Exported at: ${new Date().toISOString()}`,
  `Source root: ${sourceRoot}`,
  `Sessions: ${sessions.length}`,
  `Messages: ${sessions.reduce((sum, session) => sum + session.messageCount, 0)}`,
  "",
  "| Start time | Messages | Title | Markdown | Raw JSON |",
  "| --- | ---: | --- | --- | --- |",
  ...sessions.map((session) => {
    const markdownRel = path.relative(outputRoot, session.markdownPath);
    const rawRel = path.relative(outputRoot, session.rawPath);
    return `| ${session.startTime || "unknown"} | ${session.messageCount} | ${tableCell(session.title)} | [md](${markdownRel}) | [json](${rawRel}) |`;
  }),
  "",
];

fs.writeFileSync(path.join(outputRoot, "index.md"), indexLines.join("\n"));
fs.writeFileSync(path.join(outputRoot, "manifest.json"), JSON.stringify({ exportedAt: new Date().toISOString(), sourceRoot, sessions }, null, 2));

console.log(`Exported ${sessions.length} sessions to ${outputRoot}`);
