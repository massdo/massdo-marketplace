// Hook SubagentStart: remembers the flow and the step under which a subagent starts, so that its usage reports keep
// them even when the session has moved to another step before they are sent.
import path from "node:path";

import { agentStepFile, readHookInput, readJson, sessionDir, writeJson } from "./session-state.mjs";

const input = await readHookInput();
if (typeof input.agent_id === "string") {
  const folder = sessionDir(input.session_id);
  const step = readJson(path.join(folder, "step.json"), null);
  writeJson(agentStepFile(folder, input.agent_id), { flowId: step?.flowId ?? null, stepId: step?.stepId ?? null });
}
