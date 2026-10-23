import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'

import type { AppSession } from '../types'

const MINUTE = 60_000
const NOW = Date.parse('2026-10-22T18:00:00Z')
const DIR = '/home/t/.claude/agent-queue'
const APP = '/home/t/Library/Application Support/Claude/claude-code-sessions/acct/org'

const PANE = {
  plugin: 'agent-queue',
  component: 'Pane',
  requestId: 'agent-queue',
  props: {
    title: 'Agents',
    isFocused: true,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

const STARTED = { cwd: '/code/nestor-mcp', surface: 'desktop', isInteractive: true } as const

type Fake = {
  id: string
  cwd: string
  title?: string
  isRunning: boolean
  minutesAgo: number
  startedBy?: string
  /** The app's record of it; absent, the app keeps none. */
  app?: AppSession
}

type World = {
  self: Fake
  others: Fake[]
  shown: string[]
  focused?: string
  files: Map<string, string>
  decision?: 'allow' | 'ask' | 'deny'
  isRefused?: boolean
  /** This session lost the app's tools, as when their MCP server disconnects. */
  isToolMissing?: boolean
}

const rowOf = (one: Fake) => ({
  sessionId: one.id,
  ...(one.title !== undefined ? { title: one.title } : {}),
  cwd: one.cwd,
  isArchived: false,
  isRunning: one.isRunning,
  lastActivityAt: new Date(NOW - one.minutesAgo * MINUTE).toISOString(),
  link: `claude://claude.ai/epitaxy/${one.id}`,
  ...(one.startedBy !== undefined ? { startedBy: one.startedBy } : {}),
})

// What a directory holds, read off the files in memory.
const entriesOf = (files: Map<string, string>, path: string) => {
  const names = new Map<string, 'file' | 'dir'>()
  for (const key of files.keys()) {
    if (!key.startsWith(`${path}/`)) continue
    const [name = '', ...rest] = key.slice(path.length + 1).split('/')
    names.set(name, rest.length > 0 ? 'dir' : 'file')
  }

  return [...names].map(([name, kind]) => ({ name, kind, size: 0, mtimeMs: 0, isLink: false }))
}

// The engine beneath the plugin: the desktop app's tools and records, a shared folder in memory, and `open` recorded.
const world = (on: On, state: World) => {
  const opened: string[][] = []
  const calls: string[] = []
  const clock = mock.clock(on, { now: NOW })
  mock.env(on, { HOME: '/home/t' })
  for (const one of [state.self, ...state.others]) {
    if (one.app || one === state.self) state.files.set(`${APP}/${one.id}.json`, JSON.stringify(one.app ?? {}))
  }
  on('session.id', () => ({ value: 'cli-self' }))
  on('session.surface', () => ({ value: 'desktop' }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('command.register', () => ({ value: { command: 'x' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.log', () => ({ value: undefined }))
  on('fs.read', (_, e) => {
    if (e.path.endsWith('/scripts/next.js')) return { value: 'SCRIPT' }
    const text = state.files.get(e.path)
    if (text === undefined) throw new Error('missing')

    return { value: text }
  })
  on('fs.write', (_, e) => {
    state.files.set(e.path, e.text)

    return { value: undefined }
  })
  on('fs.list', (_, e) => ({ value: entriesOf(state.files, e.path) }))
  on('fs.exists', (_, e) => ({ value: state.files.has(e.path) || entriesOf(state.files, e.path).length > 0 }))
  // A tool this session lost falls to the kit's bottom: the check rejects, as the engine's does ("no tool named").
  on('tool.check', (_, e, next) => (state.isToolMissing ? next(e) : { decision: state.decision ?? 'allow' }))
  on('tool.call', (_, e) => {
    calls.push(String(e.tool))
    if (e.tool === 'AskUserQuestion') return { result: {}, text: state.files.get(`${DIR}/asking/cli-self.json`) }
    if (state.isRefused) return { deny: 'refused by the person' }
    if (e.tool === 'mcp__ccd_session_mgmt__get_session') return { result: {}, text: JSON.stringify(rowOf(state.self)) }
    if (e.tool === 'mcp__ccd_window__get_window_layout') {
      const panes = state.shown.map(id => ({ kind: 'session', session_id: id, focused: id === state.focused }))

      return { result: {}, text: JSON.stringify({ main_window: { tab: 'code', panes }, popout_windows: { sessions: [] } }) }
    }

    return { result: {}, text: JSON.stringify(state.others.map(rowOf)) }
  })
  on('process.run', (_, e) => {
    opened.push([...e.argv])

    return { value: { exitCode: 0, stdout: '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })

  return { clock, opened, calls }
}

const SELF: Fake = { id: 'local_self', cwd: '/code/nestor-mcp', title: 'Keybinding', isRunning: false, minutesAgo: 1 }
const HEXAGONAL: Fake = { id: 'local_a', cwd: '/code/hexagonal', title: 'Archi', isRunning: false, minutesAgo: 20 }
const THOTH: Fake = { id: 'local_b', cwd: '/code/thoth', title: 'Bug', isRunning: false, minutesAgo: 5 }

const seenAt = (minutesAgo: number) => NOW - minutesAgo * MINUTE
const fileOf = (files: Map<string, string>, name: string) => JSON.parse(files.get(`${DIR}/${name}`) ?? 'null')
const blocked = (question: string): AppSession => ({
  postTurnSummary: { status_category: 'blocked', needs_action: question },
})

test('the leader lists every session as the app does: questions, finished, working, idle; a btw under its parent', async ($, on) => {
  const files = new Map([
    [`${DIR}/seen.json`, JSON.stringify({ local_a: seenAt(60), local_b: seenAt(400), local_e: seenAt(60), local_d: seenAt(30) })],
  ])
  world(on, {
    self: {
      ...SELF,
      cwd: '/code/nestor-mcp/.claude/worktrees/feat-x',
      app: { originCwd: '/code/nestor-mcp' },
    },
    shown: ['local_self'],
    focused: 'local_self',
    files,
    others: [
      HEXAGONAL,
      // Untitled, its last turn ended on a question the person has seen and left.
      { id: 'local_b', cwd: '/code/thoth', isRunning: false, minutesAgo: 300, app: { ...blocked('Push it?'), lastFocusedAt: seenAt(10) } },
      { id: 'local_c', cwd: '/code/nestor-plugins', title: 'Mod', isRunning: true, minutesAgo: 2 },
      { id: 'local_d', cwd: '/code/adstelam', title: 'Access', isRunning: false, minutesAgo: 90 },
      // A btw of thoth's, finished while read in thoth: never blue.
      { id: 'local_e', cwd: '/code/thoth', title: 'btw: details', isRunning: false, minutesAgo: 3, startedBy: 'local_b' },
      // Its wrap-up asked nothing: the blocked verdict beneath does not count.
      {
        id: 'local_f',
        cwd: '/code/massdo',
        title: 'PR',
        isRunning: false,
        minutesAgo: 120,
        app: { ...blocked('Merge it?'), turnWrapUp: {}, lastFocusedAt: seenAt(100) },
      },
      // A session with no folder sits where the sidebar puts it.
      {
        id: 'local_g',
        cwd: '/Users/t/Library/Application Support/Claude/scratch-workspaces/a/b/scratch-1',
        title: 'Notes',
        isRunning: false,
        minutesAgo: 600,
      },
    ],
  })
  await $.session.start(STARTED)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    const rows = (await ui.findAll({ type: 'Button' })).filter(button => button.key?.startsWith('open-'))
    expect(rows.map(row => row.text)).toEqual([
      'thoth · General coding session',
      '↳ btw: details',
      'hexagonal · Archi',
      'nestor-plugins · Mod',
      'nestor-mcp · Keybinding',
      'adstelam · Access',
      'massdo · PR',
      'This computer · Notes',
    ])
    expect((await ui.find({ type: 'Text', text: /^Here/ }))?.text).toBe('Here: nestor-mcp › Keybinding')
    expect((await ui.find({ type: 'Text', text: /^question/ }))?.text).toBe('question · 5 h')
    expect(await ui.find({ type: 'Text', text: 'Push it?' })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: 'Merge it?' })).toBeUndefined()
    expect((await ui.find({ type: 'Text', text: /working/ }))?.text).toBe('working · 2 min')
    expect((await ui.find({ type: 'Text', text: / here$/ }))?.text).toBe('idle · 1 min · here')
    expect(await ui.findAll({ type: 'Text', text: /^finished/ })).toHaveLength(1)
    expect((await ui.find({ type: 'Button', key: 'next' }))?.text).toBe('Next: hexagonal › Archi')
    await ui.unmount()
  }

  // What the other sessions and the shortcut read: the new first, then the question already seen; never the btw.
  expect(fileOf(files, 'leader.json')).toEqual({ owner: 'cli-self', at: NOW })
  expect(fileOf(files, 'state.json').rows).toHaveLength(8)
  expect(fileOf(files, 'queue.json')).toEqual([
    { id: 'local_a', link: 'claude://claude.ai/epitaxy/local_a', seenAt: seenAt(60) },
    { id: 'local_b', link: 'claude://claude.ai/epitaxy/local_b', seenAt: seenAt(10) },
  ])
  expect(files.get(`${DIR}/next.js`)).toBe('SCRIPT')
})

test('a session that finishes on screen turns idle; one that finishes elsewhere turns blue', async ($, on) => {
  const state: World = {
    self: SELF,
    shown: ['local_self', 'local_split'],
    files: new Map(),
    others: [
      { id: 'local_split', cwd: '/code/split', title: 'Beside', isRunning: true, minutesAgo: 1 },
      { id: 'local_away', cwd: '/code/away', title: 'Elsewhere', isRunning: true, minutesAgo: 1 },
    ],
  }
  const { clock } = world(on, state)
  await $.session.start(STARTED)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Button', key: 'next' })).toBeUndefined()

  state.others = state.others.map(one => ({ ...one, isRunning: false, minutesAgo: 0 }))
  await clock.advance(3000)
  expect((await ui.find({ type: 'Button', key: 'next' }))?.text).toBe('Next: away › Elsewhere')
  expect(await ui.findAll({ type: 'Text', text: /^finished/ })).toHaveLength(1)
  await ui.unmount()
})

test('a session the person brought on screen in the app counts as seen, the pane closed meanwhile', async ($, on) => {
  const files = new Map([[`${DIR}/seen.json`, JSON.stringify({ local_a: seenAt(60), local_b: seenAt(60) })]])
  world(on, {
    self: SELF,
    shown: ['local_self'],
    files,
    others: [HEXAGONAL, { ...THOTH, app: { lastFocusedAt: seenAt(2) } }],
  })
  await $.session.start(STARTED)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.find({ type: 'Button', key: 'next' }))?.text).toBe('Next: hexagonal › Archi')
  expect(await ui.findAll({ type: 'Text', text: /^finished/ })).toHaveLength(1)
  await ui.unmount()
})

test('next opens the oldest finished session and turns it idle; × does it without opening', async ($, on) => {
  const files = new Map([[`${DIR}/seen.json`, JSON.stringify({ local_a: seenAt(60), local_b: seenAt(60) })]])
  const { opened } = world(on, { self: SELF, shown: ['local_self'], files, others: [HEXAGONAL, THOTH] })
  await $.session.start(STARTED)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'next' })
  expect(opened).toEqual([['open', 'claude://claude.ai/epitaxy/local_a']])
  expect((await ui.find({ type: 'Button', key: 'next' }))?.text).toBe('Next: thoth › Bug')

  await ui.press({ key: 'dismiss-local_b' })
  expect(await ui.find({ type: 'Button', key: 'next' })).toBeUndefined()
  expect(fileOf(files, 'queue.json')).toEqual([])
  await ui.unmount()
})

test('questions left unanswered stay yellow and come back round, the least recently visited first', async ($, on) => {
  const files = new Map([[`${DIR}/seen.json`, JSON.stringify({})]])
  const { opened, clock } = world(on, {
    self: SELF,
    shown: ['local_self'],
    files,
    others: [
      { id: 'local_q1', cwd: '/code/thoth', title: 'Merge', isRunning: false, minutesAgo: 300, app: { ...blocked('Merge it?'), lastFocusedAt: seenAt(30) } },
      { id: 'local_q2', cwd: '/code/web', title: 'Deploy', isRunning: false, minutesAgo: 200, app: { ...blocked('Deploy it?'), lastFocusedAt: seenAt(10) } },
    ],
  })
  await $.session.start(STARTED)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'next' })
  await clock.advance(1000)
  await ui.press({ key: 'next' })
  await clock.advance(1000)
  await ui.press({ key: 'next' })
  expect(opened.map(argv => argv[1])).toEqual([
    'claude://claude.ai/epitaxy/local_q1',
    'claude://claude.ai/epitaxy/local_q2',
    'claude://claude.ai/epitaxy/local_q1',
  ])
  expect(await ui.findAll({ type: 'Text', text: /^question/ })).toHaveLength(2)
  await ui.unmount()
})

test('a session waiting on AskUserQuestion mid-turn shows as a question', async ($, on) => {
  const files = new Map([[`${DIR}/asking/cli-c.json`, 'true']])
  world(on, {
    self: SELF,
    shown: ['local_self'],
    files,
    others: [
      { id: 'local_c', cwd: '/code/web', title: 'Choice', isRunning: true, minutesAgo: 2, app: { cliSessionId: 'cli-c' } },
      { id: 'local_d', cwd: '/code/api', title: 'Build', isRunning: true, minutesAgo: 1, app: { cliSessionId: 'cli-d' } },
    ],
  })
  await $.session.start(STARTED)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /^question/ }))?.text).toBe('question · 2 min')
  expect((await ui.find({ type: 'Text', text: /working/ }))?.text).toBe('working · 1 min')
  expect((await ui.find({ type: 'Button', key: 'next' }))?.text).toBe('Next: web › Choice')
  await ui.unmount()

  // This session's own question raises its flag while it waits, and lowers it once answered.
  const answer = await $.tool.call({ tool: 'AskUserQuestion', questions: [] } as unknown as Parameters<typeof $.tool.call>[0])
  expect(answer.text).toBe('true')
  expect(files.get(`${DIR}/asking/cli-self.json`)).toBe('false')
})

test('while another session leads, this one draws what it shares and calls nothing', async ($, on) => {
  const row = { project: 'thoth', title: 'Bug', at: seenAt(5), seenAt: seenAt(60), link: 'l', isShown: false, isFocused: false }
  const shared = {
    rows: [
      { ...row, id: 'local_b', status: 'done', age: '5 min' },
      { ...row, id: 'local_e', title: 'btw: details', status: 'idle', age: '3 min', parent: 'local_b' },
    ],
    problem: null,
  }
  const files = new Map([
    [`${DIR}/leader.json`, JSON.stringify({ owner: 'cli-other', at: NOW - 1000 })],
    [`${DIR}/state.json`, JSON.stringify(shared)],
  ])
  const { clock, calls } = world(on, { self: SELF, shown: ['local_self'], files, others: [THOTH] })
  await $.session.start(STARTED)

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.find({ type: 'Button', key: 'next' }))?.text).toBe('Next: thoth › Bug')
  expect((await ui.find({ type: 'Button', key: 'open-local_e' }))?.text).toBe('↳ btw: details')
  expect(calls).toEqual([])

  // The leader went quiet: this session takes over.
  await clock.advance(12_000)
  expect(calls).toContain('mcp__ccd_session_mgmt__list_sessions')
  expect(fileOf(files, 'leader.json').owner).toBe('cli-self')
  await ui.unmount()
})

test('a permission to give waits for the press, then shows the sessions', async ($, on) => {
  const state: World = { self: SELF, shown: ['local_self'], files: new Map(), others: [THOTH] }
  const { clock, calls } = world(on, state)
  await $.session.start(STARTED)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  state.decision = 'ask'
  const before = calls.length
  await clock.advance(3000)
  expect(calls).toHaveLength(before)
  expect(await ui.find({ type: 'Button', key: 'allow' })).toBeDefined()

  // The press may open the dialog, the person looking at this pane; the kit plays no person, so they said yes.
  state.decision = 'allow'
  await ui.press({ key: 'allow' })
  expect(calls.length).toBeGreaterThan(before)
  expect(await ui.find({ type: 'Button', key: 'allow' })).toBeUndefined()
  await ui.unmount()
})

test('a refusal pauses the polling until the person retries, a minute at most', async ($, on) => {
  const state: World = { self: SELF, shown: ['local_self'], files: new Map(), others: [] }
  const { clock, calls } = world(on, state)
  await $.session.start(STARTED)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  state.isRefused = true
  await clock.advance(3000)
  expect((await ui.find({ type: 'Text', text: /Could not/ }))?.text).toBe(
    'Could not read the sessions: refused by the person',
  )
  const asked = calls.length
  await clock.advance(9000)
  expect(calls).toHaveLength(asked)

  state.isRefused = false
  await ui.press({ key: 'retry' })
  expect(await ui.find({ type: 'Text', text: /Could not/ })).toBeUndefined()
  expect((await ui.find({ type: 'Text', text: /screen/ }))?.text).toBe('idle · 1 min · on screen')
  await ui.unmount()
})

test('a refusal nobody retries holds the shortcut queue a minute, then the leader reads again', async ($, on) => {
  const files = new Map([[`${DIR}/seen.json`, JSON.stringify({ local_b: seenAt(60) })]])
  const state: World = { self: SELF, shown: ['local_self'], files, others: [] }
  const { clock, calls } = world(on, state)
  await $.session.start(STARTED)

  // The start's own read, still in flight, is the one refused.
  state.isRefused = true
  await clock.advance(3000)
  expect(fileOf(files, 'state.json').problem).toMatchObject({ kind: 'refused', retryAt: NOW + MINUTE })
  const asked = calls.length
  await clock.advance(MINUTE - 6000)
  expect(calls).toHaveLength(asked)

  // thoth finished meanwhile; nobody opened the pane.
  state.isRefused = false
  state.others = [THOTH]
  await clock.advance(6000)
  expect(fileOf(files, 'state.json').problem).toBeNull()
  expect(fileOf(files, 'queue.json')).toEqual([
    { id: 'local_b', link: 'claude://claude.ai/epitaxy/local_b', seenAt: seenAt(60) },
  ])
})

test('a leader that lost the sessions tool lets the lease go and keeps off it a minute', async ($, on) => {
  const files = new Map([[`${DIR}/seen.json`, JSON.stringify({ local_b: seenAt(60) })]])
  const state: World = { self: SELF, shown: ['local_self'], files, others: [THOTH], isToolMissing: true }
  const { clock, calls } = world(on, state)
  await $.session.start(STARTED)
  await clock.settle()

  // Its read failed before calling anything, and it left the lease free for the next session that ticks.
  expect(fileOf(files, 'state.json').problem.kind).toBe('error')
  expect(fileOf(files, 'leader.json')).toBeNull()
  await clock.advance(9000)
  expect(fileOf(files, 'leader.json')).toBeNull()

  // Another session, which has the tool, takes it, then goes quiet: its lease runs out, this one still keeps off.
  files.set(`${DIR}/leader.json`, JSON.stringify({ owner: 'cli-other', at: clock.now() }))
  await clock.advance(MINUTE - 12_000)
  expect(fileOf(files, 'leader.json').owner).toBe('cli-other')
  expect(calls).toEqual([])

  // A minute on, it leads again, its tools back.
  state.isToolMissing = false
  await clock.advance(3000)
  expect(fileOf(files, 'leader.json')).toEqual({ owner: 'cli-self', at: NOW + MINUTE })
  expect(fileOf(files, 'state.json').problem).toBeNull()
  expect(fileOf(files, 'queue.json')).toEqual([
    { id: 'local_b', link: 'claude://claude.ai/epitaxy/local_b', seenAt: seenAt(60) },
  ])
})
