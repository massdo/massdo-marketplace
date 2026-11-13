// The program step that the hooks wait for in place of Claude, shared by announce-wait and wait-step.
import { isSessionId, thothConnection } from "./connection.mjs";
import { answerOf } from "./session-state.mjs";

/**
 * The running program step of a thoth_next_step answer, when Claude Code can sleep through it: only Claude Code
 * (CLAUDECODE=1) wakes an idle session from a hook, and the wait needs the address of Thoth and the Claude Code
 * session that authenticates its reads.
 */
export function waitedStep(input, env = process.env) {
  if (env.CLAUDECODE !== "1" || thothConnection(env) === null || !isSessionId(input.session_id)) return null;
  const answer = answerOf(input.tool_response);
  const flowId = input.tool_input?.flowId;
  if (answer?.kind !== "working" || answer.overdue !== false || typeof flowId !== "string") return null;
  return {
    sessionId: input.session_id,
    flowId,
    stepId: answer.stepId,
    startedAt: answer.startedAt,
    deadline: Date.parse(answer.startedAt) + answer.maxDurationMinutes * 60_000,
  };
}
