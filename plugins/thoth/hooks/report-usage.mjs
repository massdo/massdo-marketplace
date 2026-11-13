// Hooks Stop, SubagentStop and SessionEnd: sends to Thoth one report per request since the last report: its model,
// its date, its tokens (the 5-minute and 1-hour cache writes apart, as they are priced apart), its web searches, its
// calls of the WebSearch and WebFetch tools, whose inner requests are not in the transcript, its answer time and its
// errors, with its flow; never any text of the conversation, nothing on stdout. A request of the
// session goes to the flow the session was on at its date, and Thoth finds its step; a request of a subagent keeps
// the flow and the step the subagent started under. At the session end, the last sending says that the session ended.
import { createHash } from "node:crypto";
import { closeSync, fstatSync, openSync, readdirSync, readFileSync, readSync } from "node:fs";
import path from "node:path";

import { agentStepFile, readHookInput, readJson, sessionDir, withLock, writeJson } from "./session-state.mjs";
import { sendRequests } from "./telemetry.mjs";

const count = (value) => (Number.isInteger(value) && value > 0 ? value : 0);
const text = (value) => (typeof value === "string" && value.length > 0 ? value.slice(0, 200) : undefined);

/** The report of one request: its tokens, its searches, its answer time and its errors, never its content. */
function requestOf({ key, model, usage, at, from, errors, searches, fetches }) {
  const creation = usage.cache_creation;
  const cache =
    creation && typeof creation === "object"
      ? {
          cacheWrite5mTokens: count(creation.ephemeral_5m_input_tokens),
          cacheWrite1hTokens: count(creation.ephemeral_1h_input_tokens),
        }
      : count(usage.cache_creation_input_tokens) > 0
        ? { cacheWriteUnsplitTokens: count(usage.cache_creation_input_tokens) }
        : { cacheWrite5mTokens: 0, cacheWrite1hTokens: 0 };
  const speed = text(usage.speed);
  const inferenceGeo = text(usage.inference_geo);
  const serviceTier = text(usage.service_tier);
  return {
    requestKey: String(key).slice(0, 200),
    at: new Date(at).toISOString(),
    model: model.slice(0, 200),
    inputTokens: count(usage.input_tokens),
    outputTokens: count(usage.output_tokens),
    ...cache,
    cacheReadTokens: count(usage.cache_read_input_tokens),
    webSearches: count(usage.server_tool_use?.web_search_requests) + searches.count,
    webSearchToolCalls: searches.calls,
    webFetchToolCalls: fetches.calls,
    ...(speed ? { speed } : {}),
    ...(inferenceGeo ? { inferenceGeo } : {}),
    ...(serviceTier ? { serviceTier } : {}),
    durationMs: from === null ? 0 : Math.max(0, at - from),
    errors,
  };
}

const spent = (request) =>
  request.inputTokens +
    request.outputTokens +
    (request.cacheWrite5mTokens ?? 0) +
    (request.cacheWrite1hTokens ?? 0) +
    (request.cacheWriteUnsplitTokens ?? 0) +
    request.cacheReadTokens +
    request.webSearches +
    request.errors >
  0;

/** The requests written in a transcript after a byte offset, up to its last complete line. */
function requestsSince(transcript, from) {
  let descriptor;
  try {
    descriptor = openSync(transcript, "r");
  } catch {
    return { offset: from, requests: [] };
  }
  try {
    const size = fstatSync(descriptor).size;
    const start = from > size ? 0 : from;
    const chunk = Buffer.alloc(size - start);
    readSync(descriptor, chunk, 0, chunk.length, start);
    const end = chunk.lastIndexOf(0x0a) + 1;
    // A message spans several entries, one per block: it counts once, from the entry before it to its last block.
    const messages = new Map();
    const toolCalls = new Map();
    let previous = null;
    let last = null;
    for (const line of chunk.subarray(0, end).toString("utf8").split("\n")) {
      let entry;
      try {
        entry = JSON.parse(line);
      } catch {
        continue;
      }
      const time = Date.parse(entry?.timestamp);
      const message = entry?.message;
      const blocks = Array.isArray(message?.content) ? message.content : [];
      if (entry?.type === "assistant" && entry.isApiErrorMessage) {
        if (last) last.errors += 1;
      } else if (entry?.type === "assistant" && message?.usage && typeof message.model === "string") {
        const key = message.id ?? entry.requestId ?? entry.uuid;
        const known = messages.get(key);
        const at = Number.isNaN(time) ? (known?.at ?? previous) : time;
        const request = known ?? {
          key,
          errors: 0,
          searches: { count: 0, calls: 0 },
          fetches: { calls: 0 },
          from: previous ?? at,
        };
        Object.assign(request, { model: message.model, usage: message.usage, at });
        messages.set(key, request);
        for (const block of blocks)
          if (block?.type === "tool_use") toolCalls.set(block.id, { request, tool: block.name });
        last = request;
      } else if (entry?.type === "user") {
        const results = blocks.filter((block) => block?.type === "tool_result");
        for (const block of results) {
          const call = toolCalls.get(block.tool_use_id);
          if (!call) continue;
          if (block.is_error === true) call.request.errors += 1;
          // WebFetch has a model summarise each page in an inner request that the transcript does not keep either.
          if (call.tool === "WebFetch") call.request.fetches.calls += 1;
          if (call.tool === "WebSearch") {
            call.request.searches.calls += 1;
            if (results.length === 1) call.request.searches.count += count(entry.toolUseResult?.searchCount);
          }
        }
      }
      if (!Number.isNaN(time)) previous = time;
    }
    const requests = [...messages.values()]
      .filter((request) => request.at !== null)
      .map(requestOf)
      .filter(spent);
    return { offset: start + end, requests };
  } finally {
    closeSync(descriptor);
  }
}

/** The transcripts of the subagents of a session, which Claude Code writes beside its own as agent-<id>.jsonl. */
function subagentTranscripts(transcript) {
  const folder = path.join(transcript.replace(/\.jsonl$/u, ""), "subagents");
  try {
    return readdirSync(folder)
      .filter((name) => name.startsWith("agent-") && name.endsWith(".jsonl"))
      .map((name) => ({ file: path.join(folder, name), agentId: name.slice("agent-".length, -".jsonl".length) }));
  } catch {
    return [];
  }
}

/** The dated flows of the session, in the order thoth_next_step answered. */
function sessionFlows(folder) {
  try {
    return readFileSync(path.join(folder, "flows.jsonl"), "utf8")
      .split("\n")
      .flatMap((line) => {
        try {
          const mark = JSON.parse(line);
          return typeof mark?.at === "string" ? [{ at: Date.parse(mark.at), flowId: mark.flowId }] : [];
        } catch {
          return [];
        }
      });
  } catch {
    return [];
  }
}

/**
 * Where a request goes: a subagent's request to the flow and the step it started under; the session's own to the flow
 * of the last mark dated at or before it, without a step, which Thoth finds at its date.
 */
function placeOf(folder, agentId, flows) {
  const started = typeof agentId === "string" ? readJson(agentStepFile(folder, agentId), null) : null;
  if (typeof started?.flowId === "string")
    return () => ({
      flowId: started.flowId,
      ...(typeof started.stepId === "string" ? { stepId: started.stepId } : {}),
    });
  return (request) => {
    const at = Date.parse(request.at);
    const mark = flows.filter((each) => each.at <= at).at(-1);
    return typeof mark?.flowId === "string" ? { flowId: mark.flowId } : {};
  };
}

const input = await readHookInput();
if (typeof input.transcript_path === "string" && typeof input.session_id === "string") {
  const folder = sessionDir(input.session_id);
  const session = { file: input.transcript_path, agentId: null };
  const ended = input.hook_event_name === "SessionEnd";
  // A subagent stopped before its end never reaches SubagentStop: the session end reads what it left.
  const transcripts =
    input.hook_event_name === "SubagentStop"
      ? [{ file: input.agent_transcript_path ?? input.transcript_path, agentId: input.agent_id }]
      : ended
        ? [session, ...subagentTranscripts(input.transcript_path)]
        : [session];
  const flows = sessionFlows(folder);
  const requests = [];
  for (const { file, agentId } of transcripts) {
    const key = createHash("sha256").update(file).digest("hex").slice(0, 16);
    const cursor = path.join(folder, `cursor-${key}.json`);
    const read = withLock(`${path.basename(folder)}-${key}`, () => {
      const since = requestsSince(file, readJson(cursor, { offset: 0 }).offset ?? 0);
      writeJson(cursor, { offset: since.offset });
      return since;
    });
    const place = placeOf(folder, agentId, flows);
    for (const request of read.requests) requests.push({ ...place(request), ...request });
  }
  await sendRequests(input.session_id, requests, ended ? { at: new Date().toISOString() } : null);
}
