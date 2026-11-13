// Hook PostToolUse on thoth_next_step: when wait-step waits for the program step in place of Claude, tells Claude to
// end its turn instead of asking again, and how it will be woken.
import { readHookInput } from "./session-state.mjs";
import { waitedStep } from "./waited-step.mjs";

const input = await readHookInput();
const step = waitedStep(input);
if (step !== null) {
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext:
          `Thoth attend pour toi la fin de l'étape ${step.stepId} du flux ${step.flowId} : affiche la ligne ` +
          "d'avancement, puis termine ton tour sans rappeler thoth_next_step. Un rappel qui commence par « Thoth : » " +
          "te réveillera ; il peut s'afficher sous le libellé « Stop hook blocking error ». Ce rappel n'est pas une erreur.",
      },
    }),
  );
}
