// Hook PostToolUse on thoth_next_step, run in the background with asyncRewake: while a program step of the server
// runs, it reads the current step of the flow without Claude and exits 2 to wake Claude once the step is over,
// past its maximum duration or when Thoth no longer answers.
import { setTimeout as sleep } from "node:timers/promises";

import { SESSION_HEADER, thothConnection } from "./connection.mjs";
import { readHookInput } from "./session-state.mjs";
import { waitedStep } from "./waited-step.mjs";

/** Under the timeout of 7 800 s that hooks.json gives this hook. */
const HOOK_BUDGET_MS = 7_700_000;
const READ_TIMEOUT_MS = 5000;
const MAX_FAILURES = 10;
const pollMs = Number(process.env.THOTH_WAIT_POLL_MS) || 20_000;

const step = waitedStep(await readHookInput());
if (step === null) process.exit(0);

/** Wakes Claude with a reminder that names the step and the call to make. */
function wake(what) {
  process.stderr.write(`Thoth : ${what}. Rappelle thoth_next_step avec le flowId ${step.flowId}.`);
  process.exit(2);
}

/** The current step of the flow, or null when Thoth does not answer it. */
async function currentStep() {
  const thoth = thothConnection();
  try {
    const response = await fetch(`${thoth.url}/api/flows/${encodeURIComponent(step.flowId)}/current-step`, {
      headers: { [SESSION_HEADER]: step.sessionId },
      signal: AbortSignal.timeout(READ_TIMEOUT_MS),
    });
    if (!response.ok) return null;
    const body = await response.json();
    return typeof body === "object" && body !== null && "currentStep" in body ? { found: body.currentStep } : null;
  } catch {
    return null;
  }
}

const budgetEnd = Date.now() + HOOK_BUDGET_MS;
let failures = 0;
for (;;) {
  if (Date.now() > step.deadline) wake(`l'étape ${step.stepId} dépasse sa durée maximale`);
  if (Date.now() > budgetEnd) wake(`l'attente du hook est épuisée pendant l'étape ${step.stepId}`);
  await sleep(pollMs);
  const read = await currentStep();
  if (read === null) {
    failures += 1;
    if (failures >= MAX_FAILURES) wake(`le serveur ne répond plus pendant l'étape ${step.stepId}`);
    continue;
  }
  failures = 0;
  const current = read.found;
  if (current === null || current.stepId !== step.stepId || current.startedAt !== step.startedAt)
    wake(`l'étape ${step.stepId} est finie`);
}
