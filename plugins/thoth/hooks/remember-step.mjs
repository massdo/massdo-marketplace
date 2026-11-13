// Hook PostToolUse on thoth_next_step: remembers the last answer of the session, its flow, its step and, for an
// agent step only, its tools. Any other answer keeps the flow for the usage reports and lifts the tool restriction;
// a refusal, which says nothing of the step, only lifts the restriction. Each answer with a kind also dates the flow
// of the session in flows.jsonl, which says to which flow each request of the session goes: none after a flow is
// delivered or abandoned, until the session moves to a flow again.
import { appendFileSync, mkdirSync } from "node:fs";
import path from "node:path";

import { answerOf, readHookInput, readJson, sessionDir, writeJson } from "./session-state.mjs";

const input = await readHookInput();
const answer = answerOf(input.tool_response);
const folder = sessionDir(input.session_id);
const file = path.join(folder, "step.json");
if (typeof answer?.kind === "string") {
  const flowId = typeof input.tool_input?.flowId === "string" ? input.tool_input.flowId : null;
  writeJson(file, {
    flowId,
    stepId: typeof answer.stepId === "string" ? answer.stepId : null,
    tools: answer.kind === "agent_step" && Array.isArray(answer.tools) ? answer.tools : null,
  });
  mkdirSync(folder, { recursive: true });
  const ended = answer.kind === "delivered" || answer.kind === "abandoned";
  appendFileSync(
    path.join(folder, "flows.jsonl"),
    `${JSON.stringify({ at: new Date().toISOString(), flowId: ended ? null : flowId })}\n`,
  );
} else {
  const previous = readJson(file, null);
  if (previous !== null) writeJson(file, { ...previous, tools: null });
}
