// Hook PreToolUse on every tool: within a lot agent, refuses a tool outside the list of the agent step.
// The tools of Thoth stay allowed, the server checking their use by step, and so do the tools of Claude Code that an
// agent needs to load its tools and hand back its report; the main session is never restricted.
import path from "node:path";

import { readHookInput, readJson, sessionDir } from "./session-state.mjs";

const THOTH_TOOLS = "mcp__plugin_thoth_thoth__";
const AGENT_TOOLS = ["SubagentHandback", "ToolSearch"];

const input = await readHookInput();
const tool = String(input.tool_name ?? "");
if (typeof input.agent_id === "string" && !tool.startsWith(THOTH_TOOLS) && !AGENT_TOOLS.includes(tool)) {
  const step = readJson(path.join(sessionDir(input.session_id), "step.json"), null);
  if (Array.isArray(step?.tools) && !step.tools.includes(tool)) {
    const allowed =
      step.tools.length > 0 ? `outils permis : ${step.tools.join(", ")}` : "seuls les outils de Thoth sont permis";
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: `L'étape ${String(step.stepId)} de Thoth n'autorise pas l'outil ${tool} (${allowed}).`,
        },
      }),
    );
  }
}
