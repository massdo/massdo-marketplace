// The state that the hooks of one Claude Code session share, under $TMPDIR/thoth/<session_id>/.
import { mkdirSync, readFileSync, renameSync, rmdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

/** The folder of Thoth's hook state on this workstation. */
export const stateRoot = () => path.join(tmpdir(), "thoth");

/** The folder of a session, its id kept to letters, digits, « - » and « _ ». */
export function sessionDir(sessionId) {
  const safe = String(sessionId ?? "").replace(/[^A-Za-z0-9_-]/g, "_");
  return path.join(stateRoot(), safe === "" ? "sans-session" : safe);
}

/** The file that keeps the flow and the step under which a subagent of a session started. */
export function agentStepFile(folder, agentId) {
  return path.join(folder, "agents", `${String(agentId).replace(/[^A-Za-z0-9_-]/g, "_")}.json`);
}

/** A JSON file, or the fallback when it is missing or unreadable. */
export function readJson(file, fallback) {
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch {
    return fallback;
  }
}

/** Writes a JSON file whole: a temporary file renamed over it. */
export function writeJson(file, value) {
  mkdirSync(path.dirname(file), { recursive: true });
  const temporary = `${file}.${String(process.pid)}.tmp`;
  writeFileSync(temporary, JSON.stringify(value));
  renameSync(temporary, file);
}

/** Runs a short synchronous change under a lock folder, waiting 1 s at most for another hook to finish. */
export function withLock(name, change) {
  const lock = path.join(stateRoot(), `${name}.lock`);
  mkdirSync(stateRoot(), { recursive: true });
  let locked = false;
  for (let attempt = 0; attempt < 50 && !locked; attempt += 1) {
    try {
      mkdirSync(lock);
      locked = true;
    } catch {
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 20);
    }
  }
  try {
    return change();
  } finally {
    if (locked) rmdirSync(lock);
  }
}

/** The JSON answer of a tool of Thoth, given as text, content blocks or structured content. */
export function answerOf(response) {
  if (typeof response === "string") {
    try {
      return JSON.parse(response);
    } catch {
      return null;
    }
  }
  if (Array.isArray(response)) {
    const text = response.find((block) => block?.type === "text")?.text;
    return text === undefined ? null : answerOf(text);
  }
  if (response && typeof response === "object") {
    if (typeof response.kind === "string") return response;
    if (response.structuredContent) return answerOf(response.structuredContent);
    if (response.content) return answerOf(response.content);
  }
  return null;
}

/** The JSON input that Claude Code writes on the standard input of a hook. */
export async function readHookInput() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    return {};
  }
}
