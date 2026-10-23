// Opens the session that has waited on the person longest, as the agent-queue plugin queues it.
// Bound to a global shortcut: osascript -l JavaScript ~/.claude/agent-queue/next.js
ObjC.import('Foundation')

const DIR = `${$.NSHomeDirectory().js}/.claude/agent-queue`

const readJson = (path, fallback) => {
  const text = $.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null)
  if (text.isNil()) return fallback
  try {
    return JSON.parse(text.js)
  } catch (error) {
    return fallback
  }
}

// Why the plugin could not read the sessions, by the problem's kind: the queue is then out of date.
const BLOCKED = {
  ask: 'Queue on hold: allow Claude to read your sessions in /queue.',
  refused: 'Queue on hold: reading the sessions was refused. It tries again in 1 min, or open /queue and press Retry.',
  error: 'Queue on hold: reading the sessions failed. Open /queue and press Retry.',
}

// `--dry-run` prints the link it would open, or the notification it would show, and changes nothing.
function run(argv) {
  const app = Application.currentApplication()
  app.includeStandardAdditions = true
  const isDryRun = argv.includes('--dry-run')

  const queue = readJson(`${DIR}/queue.json`, [])
  const seen = readJson(`${DIR}/seen.json`, {})
  const { problem } = readJson(`${DIR}/state.json`, null) || {}
  // Skips what was opened since the plugin last wrote the queue: it marked each one seen when it wrote it.
  const next = queue.find(one => (seen[one.id] || 0) <= one.seenAt)
  if (!next) {
    const text = problem ? BLOCKED[problem.kind] || BLOCKED.error : 'No agent is waiting.'
    if (isDryRun) return text
    app.displayNotification(text, { withTitle: 'Agents' })

    return
  }
  if (isDryRun) return next.link

  seen[next.id] = Date.now()
  $(JSON.stringify(seen)).writeToFileAtomicallyEncodingError(`${DIR}/seen.json`, true, $.NSUTF8StringEncoding, null)
  app.openLocation(next.link)
}
