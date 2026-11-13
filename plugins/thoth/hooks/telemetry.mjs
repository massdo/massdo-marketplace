// Usage reports sent to Thoth, kept in pending.json with their address while Thoth cannot be reached.
import path from "node:path";

import { isSessionId, SESSION_HEADER, thothConnection } from "./connection.mjs";
import { readJson, stateRoot, withLock, writeJson } from "./session-state.mjs";

const TIMEOUT_MS = 5000;
/** Refusals that may pass later: the session not yet seen by an MCP call, the throttle, the server. */
const RETRIED = new Set([401, 403, 408, 429]);
/** The most requests one sending carries, as the server accepts them. */
const BATCH = 200;
const REPORTS_PATH = "/api/usage/reports";
/** Where a plugin older than 1.12.0 sent its model reports, kept in pending.json without their address. */
const LEGACY_PATH = "/api/telemetry";
const pendingFile = () => path.join(stateRoot(), "pending.json");

/**
 * Sends one body to its address under the Claude Code session that produced it, named in the body; false when it must
 * be sent again later. A body without a session identifier can never be accepted: it is dropped.
 */
async function send({ path: address, body }) {
  if (!isSessionId(body?.sessionId)) return true;
  const thoth = thothConnection();
  if (thoth === null) return false;
  try {
    const response = await fetch(`${thoth.url}${address}`, {
      method: "POST",
      headers: { "content-type": "application/json", [SESSION_HEADER]: body.sessionId },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return response.ok || (response.status < 500 && !RETRIED.has(response.status));
  } catch {
    return false;
  }
}

function keep(sendings) {
  if (sendings.length > 0)
    withLock("pending", () => writeJson(pendingFile(), [...readJson(pendingFile(), []), ...sendings]));
}

/** An entry of pending.json: a sending with its address, or a model report kept by a plugin older than 1.12.0. */
const sendingOf = (entry) =>
  typeof entry?.path === "string" && entry.body !== undefined ? entry : { path: LEGACY_PATH, body: entry };

/**
 * Sends the requests of a session, 200 at most per sending; the last sending of an ended session says so, even
 * without any request. A sending that Thoth does not take is kept for the next session.
 */
export async function sendRequests(sessionId, requests, sessionEnded) {
  const sendings = [];
  for (let first = 0; first < requests.length; first += BATCH)
    sendings.push({ path: REPORTS_PATH, body: { sessionId, requests: requests.slice(first, first + BATCH) } });
  if (sessionEnded !== null) {
    const last = sendings.at(-1);
    if (last) last.body.sessionEnded = sessionEnded;
    else sendings.push({ path: REPORTS_PATH, body: { sessionId, requests: [], sessionEnded } });
  }
  const failed = [];
  for (const sending of sendings) if (!(await send(sending))) failed.push(sending);
  keep(failed);
}

/** Sends what earlier failures kept, each to its own address; those that fail again stay. */
export async function sendPending() {
  const kept = withLock("pending", () => {
    const entries = readJson(pendingFile(), []);
    if (entries.length > 0) writeJson(pendingFile(), []);
    return entries;
  });
  const failed = [];
  for (const sending of kept.map(sendingOf)) if (!(await send(sending))) failed.push(sending);
  keep(failed);
}
