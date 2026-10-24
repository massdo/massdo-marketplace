import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { AppSession, Layout, Problem, Row, Session, Shared, Status, Waiting } from '../types'

const PANE = 'agent-queue'
const TITLE = 'Agents'
const POLL_MS = 3000
// A leader that misses three polls hands over to whichever session ticks next.
const LEASE_MS = 10_000
// A refused read is tried again after this, by itself: the refusal may have been a moment's.
// A session whose read failed, whatever the cause, keeps off the lease as long.
const RETRY_MS = 60_000
const LIST = 'mcp__ccd_session_mgmt__list_sessions'
const SELF = 'mcp__ccd_session_mgmt__get_session'
const LAYOUT = 'mcp__ccd_window__get_window_layout'
// What the sidebar calls a session with no title, and the sessions with no folder.
const UNTITLED = 'General coding session'
const NO_FOLDER = 'This computer'
const DETAIL_MAX = 120
const rows = atom({ plugin: 'agent-queue', key: 'rows' } as const, [])
const problem = atom({ plugin: 'agent-queue', key: 'problem' } as const, null)

// Claude Code's colors, fixed: a desktop draws no theme key. Grey at work, yellow for a question, blue when finished.
const DOT: Record<Status, string> = { question: '#f59e0b', done: '#3b82f6', busy: '#9ca3af', idle: '#9ca3af' }
const LABEL: Record<Status, string> = { question: 'question', done: 'finished', busy: 'working', idle: 'idle' }
const RANK: Record<Status, number> = { question: 0, done: 1, busy: 2, idle: 3 }

type $ = EngineInterface
// When the person last had each session on screen, shared with the shortcut's script.
type Seen = Record<string, number>
// The leader's hold, renewed at each tick; null once a leader whose read failed let it go.
type Lease = { owner: string; at: number }

class Refusal extends Error {}
class Unasked extends Error {}

const homeOf = async ($: $) => {
  const home = await $.env.get('HOME')
  if (!home) throw new Error('HOME is not set')

  return home
}

const folder = async ($: $) => `${await homeOf($)}/.claude/agent-queue`

const readText = async ($: $, path: string) => {
  try {
    return String(await $.fs.read(path))
  } catch {
    return undefined
  }
}

const readJson = async <T,>($: $, path: string, fallback: T): Promise<T> => {
  const text = await readText($, path)
  if (text === undefined) return fallback
  try {
    return JSON.parse(text) as T
  } catch {
    return fallback
  }
}

// Writes only on change, so the files stay still while nothing moves.
const writeText = async ($: $, path: string, text: string) => {
  if ((await readText($, path)) !== text) await $.fs.write(path, text)
}

// Asks the permission decision first, so a background poll never opens a dialog nobody sees.
const callTool = async ($: $, tool: typeof LIST | typeof SELF | typeof LAYOUT, input: object, isAsked: boolean) => {
  const { decision, reason } = await $.tool.check({ tool, input })
  if (decision === 'deny') throw new Refusal(reason ?? 'refused')
  if (decision === 'ask' && !isAsked) throw new Unasked('Claude needs to read your session list.')
  const answer = await $.tool.call({ tool, ...input } as Parameters<$['tool']['call']>[0])
  if (answer.deny !== undefined) throw new Refusal(answer.deny)
  if (answer.isError) throw new Error(answer.text ?? 'unknown error')

  return answer.text ?? ''
}

let appDir: string | undefined

// The desktop app's folder of session records, the one that holds this session's.
const appFolder = async ($: $, selfId: string) => {
  if (appDir !== undefined && (await $.fs.exists(`${appDir}/${selfId}.json`))) return appDir
  appDir = undefined
  const root = `${await homeOf($)}/Library/Application Support/Claude/claude-code-sessions`
  const dirsOf = async (path: string) => (await $.fs.list(path).catch(() => [])).filter(one => one.kind === 'dir')
  for (const account of await dirsOf(root)) {
    for (const org of await dirsOf(`${root}/${account.name}`)) {
      const dir = `${root}/${account.name}/${org.name}`
      if (await $.fs.exists(`${dir}/${selfId}.json`)) return (appDir = dir)
    }
  }

  return undefined
}

// The app's records of these sessions, by id; none where the app keeps them elsewhere.
const appFiles = async ($: $, selfId: string, sessions: readonly Session[]) => {
  const files = new Map<string, AppSession>()
  const dir = await appFolder($, selfId)
  if (dir === undefined) return files
  for (const one of sessions) {
    const file = await readJson<AppSession | null>($, `${dir}/${one.sessionId}.json`, null)
    if (file) files.set(one.sessionId, file)
  }

  return files
}

// The app's own rule: a wrap-up's question overrides the turn's verdict, which waits on the person when blocked.
const questionOf = (file: AppSession | undefined) => {
  const summary = file?.postTurnSummary
  if (summary?.status_category === 'failed') return undefined
  if (file?.turnWrapUp) return file.turnWrapUp.needsUser
  const isBlocked = summary?.status_category === 'blocked' || summary?.status_category === 'need_input'

  return isBlocked ? (summary?.needs_action ?? '') : undefined
}

const shorten = (text: string) => {
  const line = text.replace(/\s+/g, ' ').trim()

  return line.length > DETAIL_MAX ? `${line.slice(0, DETAIL_MAX - 1)}…` : line
}

// The project as the sidebar groups it: a worktree under its repository, a session with no folder apart.
const projectOf = (path: string) => {
  if (path.includes('/Claude/scratch-workspaces/')) return NO_FOLDER
  const root = path.replace(/\/\.claude\/worktrees\/[^/]+\/?$/, '')

  return root.split('/').filter(Boolean).pop() ?? root
}

const panesOf = (layout: Layout) => (layout.main_window?.tab === 'code' ? (layout.main_window.panes ?? []) : [])

const onScreen = (layout: Layout) => {
  const popouts = (layout.popout_windows?.sessions ?? []).map(one => (typeof one === 'string' ? one : one.session_id))

  return new Set([...panesOf(layout).map(pane => pane.session_id), ...popouts])
}

const ageOf = (ms: number) => {
  const minutes = Math.floor(ms / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min`
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)} h`

  return `${Math.floor(minutes / (24 * 60))} d`
}

const byRank = (a: Row, b: Row) =>
  RANK[a.status] - RANK[b.status] || (a.status === 'idle' ? b.at - a.at : a.at - b.at)

// Questions, finished and working wait their turn oldest first; idle shows the latest first.
// A session's btws and forks sit under it, as the app keeps them inside it.
const arrange = (list: readonly Row[]) => {
  const ids = new Set(list.map(row => row.id))
  const isNested = (row: Row) => row.parent !== undefined && ids.has(row.parent)
  const withChildren = (row: Row): Row[] => [
    row,
    ...list
      .filter(one => one.parent === row.id)
      .sort((a, b) => b.at - a.at)
      .flatMap(withChildren),
  ]

  return list
    .filter(row => !isNested(row))
    .sort(byRank)
    .flatMap(withChildren)
}

const isNew = (row: Row) => row.at > row.seenAt

// Who waits on the person, for Next and the shortcut: what is new first, oldest first; then the questions already
// seen, the least recently visited first, so one left unanswered comes back round. A btw or a fork never: it lives in
// its parent.
const queueOf = (list: readonly Row[]) =>
  list
    .filter(row => row.parent === undefined && !row.isShown && (row.status === 'question' || row.status === 'done'))
    .sort((a, b) => Number(isNew(b)) - Number(isNew(a)) || (isNew(a) ? a.at - b.at : a.seenAt - b.seenAt))

// A session in the middle of a turn that waits on the person raised this flag (see `whileAsking`).
const isAsking = async ($: $, dir: string, file: AppSession | undefined) =>
  file?.cliSessionId !== undefined && (await readText($, `${dir}/asking/${file.cliSessionId}.json`)) === 'true'

// What the leader saw, turned into rows; also the seen marks and the shortcut's queue it shares.
const rank = async ($: $, dir: string, sessions: readonly Session[], layout: Layout, files: Map<string, AppSession>) => {
  const held = await readJson<Seen>($, `${dir}/seen.json`, {})
  const shown = onScreen(layout)
  const focused = panesOf(layout).find(pane => pane.focused)?.session_id
  const now = await $.clock.now()
  const all = sessions.filter(one => !one.isArchived)
  const seen: Seen = {}
  for (const one of all) {
    const at = Date.parse(one.lastActivityAt)
    // An idle one counts as seen at first sight, a running one finishes unseen; brought on screen since, it is seen.
    const before = Math.max(held[one.sessionId] ?? (one.isRunning ? 0 : at), files.get(one.sessionId)?.lastFocusedAt ?? 0)
    seen[one.sessionId] = shown.has(one.sessionId) && !one.isRunning ? Math.max(before, at) : before
  }
  await writeText($, `${dir}/seen.json`, JSON.stringify(seen))

  const list: Row[] = []
  for (const one of all) {
    const file = files.get(one.sessionId)
    const at = Date.parse(one.lastActivityAt)
    const seenAt = seen[one.sessionId] ?? 0
    const parent = file?.spawnedFrom?.sessionId ?? one.startedBy ?? one.parentSessionId
    const question = one.isRunning ? undefined : questionOf(file)
    // A btw's or a fork's own end is read in its parent: it never turns blue.
    const status: Status = one.isRunning
      ? (await isAsking($, dir, file))
        ? 'question'
        : 'busy'
      : question !== undefined
        ? 'question'
        : at > seenAt && parent === undefined
          ? 'done'
          : 'idle'
    list.push({
      id: one.sessionId,
      project: projectOf(file?.originCwd ?? one.cwd),
      title: one.title || UNTITLED,
      status,
      at,
      seenAt,
      age: ageOf(now - at),
      link: one.link ?? `claude://claude.ai/epitaxy/${one.sessionId}`,
      isShown: shown.has(one.sessionId),
      isFocused: one.sessionId === focused,
      ...(parent !== undefined ? { parent } : {}),
      ...(question ? { detail: shorten(question) } : {}),
    })
  }
  const queue: Waiting[] = queueOf(list).map(({ id, link, seenAt }) => ({ id, link, seenAt }))
  await writeText($, `${dir}/queue.json`, JSON.stringify(queue))

  return arrange(list)
}

// The leader reads the app for every session and shares what it saw in state.json; failing, it stands down.
const poll = async ($: $, isAsked: boolean) => {
  const dir = await folder($)
  const held = await readJson<Shared | null>($, `${dir}/state.json`, null)
  const now = await $.clock.now()
  // A refusal waits RETRY_MS or the person's retry: asking again at once would only be refused again.
  if (held?.problem?.kind === 'refused' && !isAsked && now < (held.problem.retryAt ?? 0)) return

  let shared: Shared
  try {
    const others = JSON.parse(await callTool($, LIST, { limit: 50 }, isAsked)) as Session[]
    const self = JSON.parse(await callTool($, SELF, { session_id: 'self' }, isAsked)) as Session
    const layout = JSON.parse(await callTool($, LAYOUT, {}, isAsked)) as Layout
    const sessions = [self, ...others]
    shared = { rows: await rank($, dir, sessions, layout, await appFiles($, self.sessionId, sessions)), problem: null }
  } catch (error) {
    const kind: Problem['kind'] = error instanceof Refusal ? 'refused' : error instanceof Unasked ? 'ask' : 'error'
    const text = error instanceof Error ? error.message : String(error)
    shared = {
      rows: held?.rows ?? [],
      problem: kind === 'refused' ? { kind, text, retryAt: now + RETRY_MS } : { kind, text },
    }
  }
  await writeText($, `${dir}/state.json`, JSON.stringify(shared))
  if (shared.problem) await standDown($)
}

// Every session draws what the leader shared, with the marks made since (a click, the shortcut) applied at once.
const load = async ($: $) => {
  const dir = await folder($)
  const shared = await readJson<Shared | null>($, `${dir}/state.json`, null)
  if (!shared) return

  const seen = await readJson<Seen>($, `${dir}/seen.json`, {})
  const list = arrange(
    shared.rows.map(row => {
      const seenAt = Math.max(row.seenAt, seen[row.id] ?? 0)

      return { ...row, seenAt, status: row.status === 'done' && seenAt >= row.at ? ('idle' as const) : row.status }
    }),
  )
  if (JSON.stringify(await read($, rows)) !== JSON.stringify(list)) await update($, rows, () => list)
  if (JSON.stringify(await read($, problem)) !== JSON.stringify(shared.problem)) {
    await update($, problem, () => shared.problem)
  }
}

// When this session may take the lease again by itself, after a read of its failed (see `standDown`).
let leadsAgainAt = 0

const holdsLease = async ($: $, isTaken: boolean) => {
  const path = `${await folder($)}/leader.json`
  const me = await $.session.id()
  const now = await $.clock.now()
  const lease = await readJson<Lease | null>($, path, null)
  if (!isTaken && lease?.owner !== me && now < leadsAgainAt) return false
  if (!isTaken && lease && lease.owner !== me && now - lease.at < LEASE_MS) return false
  await $.fs.write(path, JSON.stringify({ owner: me, at: now }))

  return true
}

// A leader whose read failed lets the lease go and keeps off it RETRY_MS, unless the person presses for it:
// the failure may be this session's alone (a tool it lost, its project's permissions), so another one reads meanwhile.
const standDown = async ($: $) => {
  const path = `${await folder($)}/leader.json`
  const lease = await readJson<Lease | null>($, path, null)
  if (lease?.owner === (await $.session.id())) await $.fs.write(path, JSON.stringify(null))
  leadsAgainAt = (await $.clock.now()) + RETRY_MS
}

// Only a session of the desktop app has the app's session tools: one in a terminal, even on the same transcript,
// never leads. Asked at each tick, since a surface may attach after the start.
const canLead = async ($: $) => (await $.session.surfaces()).includes('desktop')

let isTicking = false

// `isAsked`: the person pressed for it, so this session leads and may show a permission dialog.
const tick = async ($: $, isAsked = false) => {
  if (isTicking && !isAsked) return
  isTicking = true
  try {
    if ((await canLead($)) && (await holdsLease($, isAsked))) await poll($, isAsked)
    await load($)
  } finally {
    isTicking = false
  }
}

const logged = ($: $, work: Promise<unknown>) =>
  work.catch(error => $.ui.log(`agent-queue: ${String(error)}`, { to: 'debug' }))

const markSeen = async ($: $, id: string) => {
  const path = `${await folder($)}/seen.json`
  const seen = await readJson<Seen>($, path, {})
  await $.fs.write(path, JSON.stringify({ ...seen, [id]: await $.clock.now() }))
}

// The global shortcut runs this copy, at a path that stays put when the plugin updates.
const installScript = async ($: $) => {
  const source = await readText($, `${$.plugin.root}/scripts/next.js`)
  if (source !== undefined) await writeText($, `${await folder($)}/next.js`, source)
}

// A finished session turns idle once visited, as in herdr; a question goes to the back of the queue.
const openSession = async ($: $, row: Row) => {
  const { exitCode } = await $.process.run(['open', row.link])
  if (exitCode !== 0) {
    $.ui.toast('Could not open this session.')

    return
  }
  await markSeen($, row.id)
  await logged($, tick($))
}

const openNext = async ($: $) => {
  await logged($, tick($))
  const next = queueOf(await read($, rows))[0]
  if (!next) {
    $.ui.toast('No agent is waiting.')

    return
  }
  await openSession($, next)
}

// Raises this session's flag for the leader while `run` waits on the person (AskUserQuestion, ExitPlanMode).
const whileAsking = async <T,>($: $, run: () => Promise<T>) => {
  const path = `${await folder($)}/asking/${await $.session.id()}.json`
  await logged($, $.fs.write(path, 'true'))
  try {
    return await run()
  } finally {
    await logged($, $.fs.write(path, 'false'))
  }
}

const dismiss = async ($: $, id: string) => {
  await markSeen($, id)
  await logged($, tick($))
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'open-agent-queue',
      description: 'Opens the agents pane: every session and what it waits for',
    })
    await $.command.register({
      name: 'next',
      description: 'Goes to the agent that has waited on you longest',
    })
    await logged($, installScript($))
    // The pane opens on /open-agent-queue only: the shortcut needs nothing drawn, just this polling.
    void logged($, tick($))
    $.clock.every(POLL_MS, () => void logged($, tick($)))

    return next(e)
  })

  // A question asked mid-turn: the session runs, yet waits on the person. A failure here never holds the tool.
  on('tool.call', { tool: 'AskUserQuestion' }, ($, e, next) => whileAsking($, () => next(e))).catch(($, e, next) =>
    next(e),
  )
  on('tool.call', { tool: 'ExitPlanMode' }, ($, e, next) => whileAsking($, () => next(e))).catch(($, e, next) =>
    next(e),
  )

  on('command.run', { command: 'open-agent-queue' }, async $ => {
    await $.ui.open({ id: PANE, title: TITLE, focus: true })

    return {}
  })

  on('command.run', { command: 'next' }, async $ => {
    await openNext($)

    return {}
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Button, Text } = $.ui.resolve(e)
    const list = await read($, rows)
    const trouble = await read($, problem)
    const next = queueOf(list)[0]
    const here = list.find(row => row.isFocused)
    const parentOf = (row: Row) => list.find(one => one.id === row.parent)
    // Where a session sits, as the sidebar shows it: its project, then the session it lives in.
    const placeOf = (row: Row) => [row.project, parentOf(row)?.title, row.title].filter(Boolean).join(' › ')

    return (
      <Box flexDirection="column">
        {here && <Text weight="semibold">Here: {placeOf(here)}</Text>}
        {trouble?.kind === 'ask' && (
          <Box flexDirection="column">
            <Text dimColor>{trouble.text}</Text>
            <Button key="allow" variant="primary" label="Allow" onPress={() => tick($, true)} />
          </Box>
        )}
        {trouble && trouble.kind !== 'ask' && (
          <Box flexDirection="column">
            <Text dimColor>Could not read the sessions: {trouble.text}</Text>
            <Button key="retry" label="Retry" onPress={() => tick($, true)} />
          </Box>
        )}
        {!trouble && list.length === 0 && <Text dimColor>Loading sessions…</Text>}
        {next && (
          <Button key="next" hotkey="n" variant="primary" onPress={() => openNext($)}>
            Next: {placeOf(next)}
          </Button>
        )}
        {list.map((row, i) => {
          const isNested = parentOf(row) !== undefined
          const name = isNested ? `↳ ${row.title}` : `${row.project} · ${row.title}`

          return (
            <Box
              key={`row-${row.id}`}
              flexDirection="column"
              marginLeft={isNested ? 2 : 0}
              {...(row.isFocused ? { borderStyle: 'round', borderColor: DOT.busy } : {})}
            >
              <Box flexDirection="row">
                <Text color={DOT[row.status]}>{row.status === 'idle' ? '○ ' : '● '}</Text>
                <Button
                  key={`open-${row.id}`}
                  plain
                  hotkey={i < 9 ? String(i + 1) : undefined}
                  onPress={() => openSession($, row)}
                >
                  {row.isFocused ? <Text weight="bold">{name}</Text> : name}
                </Button>
                {row.status === 'done' && (
                  <Button key={`dismiss-${row.id}`} plain label="×" onPress={() => dismiss($, row.id)} />
                )}
              </Box>
              <Box paddingLeft={2}>
                <Text dimColor>
                  {LABEL[row.status]} · {row.age}
                  {row.isFocused ? ' · here' : row.isShown ? ' · on screen' : ''}
                </Text>
              </Box>
              {row.detail && (
                <Box paddingLeft={2}>
                  <Text color={DOT.question}>{row.detail}</Text>
                </Box>
              )}
            </Box>
          )
        })}
      </Box>
    )
  })
}
