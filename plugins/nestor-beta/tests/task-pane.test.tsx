import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'nestor-beta',
  component: 'Pane',
  requestId: 'nestor-taches',
  props: {
    title: 'Nestor · Skyline',
    isFocused: true,
    bodyColumns: 80,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 60 },
    view: {},
  },
} as const

const RUN = {
  command: 'nestor-taches',
  origin: { kind: 'composer' },
  presentation: { isFullscreen: false, columns: 80 },
} as const

const STARTED = { cwd: '/code/skyline', surface: 'desktop', isInteractive: true } as const
const LIST = 'mcp__plugin_nestor_nestor__list_items'
const UPDATE = 'mcp__plugin_nestor_nestor__update_item'
const CREATE = 'mcp__plugin_nestor_nestor__create_item'
const BUILD = 'mcp__plugin_nestor_nestor__manage_build'
const SERVER = 'plugin_nestor_nestor'
// What the server accepts from nestor-beta: its prefix 2, then 16 lowercase hex characters.
const NESTOR_BETA_HASH = /^2[0-9a-f]{16}$/
const SKYLINE = { id: 'QYQi', name: 'Skyline' }
const SCOPE = { mode: 'project', projectId: 'QYQi' }

const PLAN = {
  id: 'p1',
  type: 'plan',
  title: 'refonte de l’architecture',
  slug: 'silver_whitefish',
  excerpt: 'Refonte complète.',
  version: 3,
  workRevision: 2,
  approval: { workRevision: 2, approvedAt: '2026-10-20T10:00:00Z' },
  progress: 'in_progress',
  project: SKYLINE,
}

const TASK = {
  id: 't1',
  type: 'task',
  title: 'migration du core et de l’API publique',
  slug: 'scarlet_tiglon',
  excerpt: 'Migrer le core puis l’API.',
  version: 1,
  status: 'ready_to_build',
  priority: 'high',
  dueAt: { date: '2099-10-27', isAllDay: true },
  backlog: false,
  planId: 'p1',
  template: 'code',
  workRevision: 1,
  approval: { workRevision: 1, approvedAt: '2026-10-21T10:00:00Z' },
  project: SKYLINE,
  tags: [{ id: 'g1', name: 'core' }],
}

const ORPHAN = {
  id: 't2',
  type: 'task',
  title: 'corriger le login',
  slug: 'amber_koala',
  excerpt: '',
  version: 1,
  status: 'todo',
  priority: 'normal',
  dueAt: { date: '2020-01-15', isAllDay: true },
  backlog: false,
  project: SKYLINE,
}

const LATER = {
  id: 't3',
  type: 'task',
  title: 'traduire la documentation',
  slug: 'teal_otter',
  excerpt: '',
  version: 1,
  status: 'todo',
  priority: 'low',
  backlog: true,
  project: SKYLINE,
}

const NOTE = {
  id: 'n2',
  type: 'note',
  title: 'compte rendu du lancement',
  slug: 'olive_heron',
  excerpt: 'Notes du lancement.',
  version: 1,
  project: SKYLINE,
}

const COUNTS = {
  inbox: 0,
  today: 0,
  upcoming: 0,
  backlog: 1,
  completed: 0,
  cancelled: 0,
  recent: 0,
  active: 3,
  agenda: 0,
}

const pageOf = (items: unknown[], rest: Record<string, unknown> = {}) => ({
  view: 'active',
  items,
  totalCount: items.length,
  taskViewCounts: COUNTS,
  hasMore: false,
  ...rest,
})

const { excerpt: _excerpt, ...TASK_DETAIL } = TASK
const READ = {
  item: {
    ...TASK_DETAIL,
    body: 'Corps de la tâche.',
    specification: {
      context: 'Le core d’abord.',
      steps: [{ action: 'Migrer le core', verification: 'pnpm test' }],
      doneWhen: ['tests verts'],
    },
  },
  project: SKYLINE,
  tags: [],
  relations: [],
  etag: 'e1',
}

type Call = Record<string, unknown>

type Pages = { first: unknown[]; next?: unknown[]; backlog?: unknown[] }

// A test's own answers, before the defaults: to a tool call Claude makes, or to the pane's own server call.
type Answers = {
  tool?: (call: Call) => unknown
  mcp?: (tool: string, args: Call) => unknown
}

// The engine beneath the mod: a Nestor server answering from memory, and what the mod opens, closes and submits.
const world = (
  on: On,
  pages: Pages,
  tools = [{ name: LIST, description: '', mcp: true }],
  answers: Answers = {},
) => {
  const calls: Call[] = []
  const reads: Call[] = []
  const opened: string[] = []
  const closed: string[] = []
  const submitted: Call[] = []
  const toasts: string[] = []
  // Set to a message, every $.mcp.call rejects with it, as an unreachable server does; tools narrows it.
  const outage: { message: string | null; tools?: string[] } = { message: null }
  const panes: {
    id: string
    title: string
    isShown: boolean
    isFocused: boolean
    isPlaced: boolean
  }[] = []
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('command.register', () => ({ value: { command: 'nestor-taches' } }))
  on('ui.open', (_, e) => {
    opened.push(e.title ?? e.id)

    return { value: { isPlaced: true } }
  })
  on('ui.close', (_, e) => {
    closed.push(e.id)

    return { value: undefined }
  })
  on('ui.panes', () => ({ value: panes }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.toast', (_, e) => {
    toasts.push(e.text)

    return { value: undefined }
  })
  on('ui.log', () => ({ value: undefined }))
  on('tool.check', () => ({ decision: 'allow' }))
  on('tool.list', () => ({ value: tools }))
  on('command.run', (_, e) => {
    submitted.push({ command: e.command, args: e.args })

    return { text: 'skill lancé' }
  })
  const listPage = (args: Call) =>
    args.view === 'backlog'
      ? pageOf(pages.backlog ?? [], { view: 'backlog' })
      : args.cursor === 'c1'
        ? pageOf(pages.next ?? [])
        : pageOf(pages.first, pages.next ? { hasMore: true, nextCursor: 'c1' } : {})
  on('tool.call', (_, e) => {
    const call = e as unknown as Call
    calls.push(call)
    const payload =
      answers.tool?.(call) ??
      (e.tool.endsWith('__list_items')
      ? listPage(call)
      : e.tool.endsWith('__update_item') || e.tool.endsWith('__manage_build')
        ? {
            item: {
              id: call.ref,
              type: 'task',
              version: 2,
              status: call.status,
              slug: 'scarlet_tiglon',
            },
            etag: 'e2',
          }
        : e.tool.endsWith('__create_item')
          ? {
              item: { id: 'n1', type: call.type, version: 1, status: 'todo', slug: 'new_newt' },
              etag: 'e3',
            }
          : {})
    const text = JSON.stringify(payload)

    return {
      result: { content: [{ type: 'text', text }], isError: false, structuredContent: payload },
      text,
    }
  })
  // The server's own answers carry text blocks alone, as the MCP SDK hands them to a plugin.
  on('mcp.call', (_, e) => {
    const args = e.args
    reads.push({ server: e.server, tool: e.tool, ...args })
    if (outage.message !== null && (outage.tools === undefined || outage.tools.includes(e.tool))) {
      throw new Error(outage.message)
    }
    const payload =
      answers.mcp?.(e.tool, args) ??
      (e.tool === 'get_item'
        ? READ
        : e.tool === 'list_items'
          ? listPage(args)
          : e.tool === 'get_project'
            ? args.name === 'Skyline'
              ? { ...SKYLINE, normalizedName: 'skyline', version: 1 }
              : null
            : e.tool === 'search_project'
              ? { items: [], totalCount: 0, hasMore: false }
              : {})
    if (payload === null) {
      return {
        value: { content: [{ type: 'text', text: '{"error":"NOT_FOUND"}' }], isError: true },
      }
    }

    return { value: { content: [{ type: 'text', text: JSON.stringify(payload) }], isError: false } }
  })

  return { calls, reads, opened, closed, submitted, panes, toasts, outage }
}

const titles = async (ui: {
  findAll: (q: { type: string; text: RegExp }) => Promise<{ text: string }[]>
}) =>
  (await ui.findAll({ type: 'Text', text: /^[^▸▾]/ }))
    .map(one => one.text)
    .filter(text => [PLAN, TASK, ORPHAN, LATER].some(item => item.title === text))

test('a next-tasks read fills the pane: the plan, its task beneath, the orphan after, with quiet status lines', async ($, on) => {
  const { opened } = world(on, { first: [TASK, PLAN], next: [ORPHAN] })
  await $.session.start(STARTED)

  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  await $.tool.call({ tool: LIST, version_hash: 'h1', cursor: 'c1' })
  expect(opened).toContain('Nestor · Skyline')

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await titles(ui)).toEqual([PLAN.title, TASK.title, ORPHAN.title])
    expect((await ui.find({ type: 'Button', key: 'row:p1' }))?.text).toBe(
      `◐ ${PLAN.title} · plan · en cours`,
    )
    expect((await ui.find({ type: 'Button', key: 'row:t1' }))?.text).toBe(
      `● ${TASK.title} · prête à build · ↑ haute · échéance 27 oct.`,
    )
    expect((await ui.find({ type: 'Button', key: 'row:t2' }))?.text).toBe(
      `○ ${ORPHAN.title} · à faire · en retard, échéance 15 janv.`,
    )
    expect(await ui.findAll({ type: 'Text', text: /[›⌄]/ })).toEqual([])
    expect(await ui.findAll({ type: 'Button', text: /[›⌄]/ })).toEqual([])
    expect(
      (await ui.findAll({ type: 'Text', text: /^(Plans|Tâches)$/ })).map(one => one.text),
    ).toEqual(['Plans', 'Tâches'])
    expect(await ui.find({ type: 'Text', text: /^plan$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^en cours$/ })).toBeDefined()
    const ready = await ui.find({ type: 'Text', text: /^prête à build$/ })
    expect(ready?.props.dimColor).toBe(true)
    expect(ready?.props.color).toBeUndefined()
    expect((await ui.find({ type: 'Text', text: /^●$/ }))?.props.color).toBe('claude')
    expect(await ui.find({ type: 'Text', text: /^↑ haute$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /^échéance 27 oct\.$/ })).toBeDefined()
    expect(
      (await ui.find({ type: 'Text', text: /^en retard, échéance 15 janv\.$/ }))?.props.color,
    ).toBe('error')
    for (const one of await ui.findAll({ type: 'Text' })) {
      expect(one.props.backgroundColor).toBeUndefined()
      expect(String(one.props.color ?? '').startsWith('#')).toBe(false)
    }
    const name = await ui.find({ type: 'Text', text: /^Skyline$/ })
    expect(name?.props.size).toBe('title')
    expect(name?.props.color).toBeUndefined()
    // The desktop pane's own header already has a close control.
    const close = await ui.find({ type: 'Button', key: 'close' })
    expect(close === undefined).toBe(surface === 'desktop')
    expect((await ui.find({ type: 'Text', text: /actives/ }))?.text).toMatch(
      /^3 actives · 1 en backlog · lu à \d\d:\d\d$/,
    )
    await ui.unmount()
  }
})

const CONNECTOR = 'aa0a02b5-f069-4e28-9150-4f77a92e0089'
const CONNECTOR_TOOLS = [
  { name: `mcp__${CONNECTOR}__list_items`, description: 'Lists journal items.', mcp: true },
]

test('Nestor listed under a connector id still fills the pane, which then reads through that server', async ($, on) => {
  const { opened, reads } = world(on, { first: [PLAN, TASK] }, CONNECTOR_TOOLS)
  await $.session.start(STARTED)

  await $.tool.call({ tool: 'mcp__other__list_items', scope: SCOPE, view: 'active' })
  expect(opened).toEqual([])

  await $.tool.call({
    tool: `mcp__${CONNECTOR}__list_items`,
    version_hash: 'h1',
    scope: SCOPE,
    view: 'active',
  })
  expect(opened).toEqual(['Nestor · Skyline'])
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await titles(ui)).toEqual([PLAN.title, TASK.title])
  await ui.press({ key: 'row:t1' })
  await ui.press({ key: 'detail:t1' })
  expect(reads[0]).toMatchObject({
    server: CONNECTOR,
    tool: 'get_item',
    version_hash: 'h1',
    ref: 't1',
  })
  await ui.unmount()
})

test('beside a connector, the pane reads through the nestor plugin’s own server', async ($, on) => {
  const { reads } = world(on, { first: [PLAN, TASK] }, [
    ...CONNECTOR_TOOLS,
    { name: LIST, description: '', mcp: true },
  ])
  await $.session.start(STARTED)
  await $.tool.call({
    tool: `mcp__${CONNECTOR}__list_items`,
    version_hash: 'h1',
    scope: SCOPE,
    view: 'active',
  })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'refresh' })
  expect(reads[0]).toMatchObject({ server: SERVER, tool: 'list_items', version_hash: 'h1' })
  await ui.unmount()
})

test('without a read, the pane finds Nestor in the tool list by its description', async ($, on) => {
  const { reads } = world(on, { first: [ORPHAN] }, CONNECTOR_TOOLS)
  await $.session.start(STARTED)

  expect(await $.command.run({ ...RUN, args: 'Skyline' })).toEqual({
    text: 'Panneau Nestor ouvert sur Skyline.',
  })
  expect(reads[0]).toMatchObject({ server: CONNECTOR, tool: 'get_project', name: 'Skyline' })
  for (const one of reads) {
    expect(String(one.version_hash)).toMatch(NESTOR_BETA_HASH)
  }
})

test('a row unfolds on press; Lire le détail reads the item alone and draws its body', async ($, on) => {
  const { calls, reads } = world(on, { first: [PLAN, TASK] })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /approbation/ })).toBeUndefined()

  await ui.press({ key: 'row:t1' })
  expect((await ui.find({ type: 'Text', text: /approbation/ }))?.text).toBe(
    'scarlet_tiglon · tâche code · approbation courante',
  )
  expect((await ui.find({ type: 'Text', text: /#core/ }))?.text).toBe('#core')
  expect((await ui.find({ type: 'Text', text: /Migrer le core puis/ }))?.text).toBe(
    'Migrer le core puis l’API.',
  )

  await ui.press({ key: 'detail:t1' })
  expect(calls.filter(call => call.tool !== LIST)).toHaveLength(0)
  expect(reads).toHaveLength(1)
  expect(reads[0]).toMatchObject({
    server: SERVER,
    tool: 'get_item',
    version_hash: 'h1',
    scope: SCOPE,
    ref: 't1',
    known: null,
  })
  const body = await ui.find({ type: 'Markdown', text: /Corps de la tâche/ })
  expect(body?.text).toContain('### Spécification')
  expect(body?.text).toContain('1. Migrer le core — vérification : pnpm test')
  expect(body?.text).toContain('- tests verts')
  expect(await ui.find({ type: 'Button', key: 'detail:t1' })).toBeUndefined()

  await ui.press({ key: 'fold' })
  expect(await ui.find({ type: 'Text', text: /approbation/ })).toBeUndefined()
  await ui.unmount()
})

test('a second press on a row folds its detail, and so does Replier, last in the detail of a task, a plan or a note', async ($, on) => {
  world(on, { first: [PLAN, TASK, NOTE] })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })

  const keysOf: Record<string, string[]> = {
    t1: ['row:t1', 'detail:t1', 'spec:t1', 'build:t1', 'fold:t1'],
    p1: ['row:p1', 'detail:p1', 'spec:p1', 'build:p1', 'fold:p1'],
    n2: ['row:n2', 'detail:n2', 'fold:n2'],
  }
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    for (const [id, keys] of Object.entries(keysOf)) {
      const fold = { type: 'Button', key: `fold:${id}` }
      expect(await ui.find(fold)).toBeUndefined()

      await ui.press({ key: `row:${id}` })
      const buttons = await ui.findAll({ type: 'Button' })
      expect(buttons.map(one => one.key).filter(key => key?.endsWith(`:${id}`))).toEqual(keys)
      expect((await ui.find(fold))?.text).toBe('Replier')

      await ui.press({ key: `row:${id}` })
      expect(await ui.find(fold)).toBeUndefined()

      await ui.press({ key: `row:${id}` })
      await ui.press({ key: `fold:${id}` })
      expect(await ui.find(fold)).toBeUndefined()
      expect(await ui.find({ type: 'Button', key: `row:${id}` })).toBeDefined()
    }
    await ui.unmount()
  }
})

test('Spec and Build run the skill on the clicked item', async ($, on) => {
  const { submitted } = world(on, { first: [PLAN, TASK, ORPHAN] })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'row:t1' })
  expect((await ui.find({ type: 'Text', text: /^Build$/ }))?.props.color).toBe('claude')
  await ui.press({ key: 'build:t1' })
  await ui.press({ key: 'spec:t1' })
  expect(submitted).toEqual([
    { command: 'nestor-beta:build', args: 'scarlet_tiglon' },
    { command: 'nestor-beta:spec', args: 'scarlet_tiglon project:QYQi' },
  ])

  // A todo task has no Build; a plan with a current approval has one.
  await ui.press({ key: 'row:t2' })
  expect(await ui.find({ type: 'Button', key: 'build:t2' })).toBeUndefined()
  expect(await ui.find({ type: 'Button', key: 'spec:t2' })).toBeDefined()
  await ui.press({ key: 'row:p1' })
  expect(await ui.find({ type: 'Button', key: 'build:p1' })).toBeDefined()
  await ui.unmount()
})

test('a mutation Claude makes updates the row; a task created in the project joins the list', async ($, on) => {
  world(on, { first: [PLAN, TASK] })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await $.tool.call({
    tool: BUILD,
    version_hash: 'h1',
    scope: SCOPE,
    operation: 'reserve',
    ref: 't1',
    status: 'building',
  })
  expect((await ui.find({ type: 'Text', text: /^build en cours$/ }))?.text).toBe('build en cours')
  expect(await ui.find({ type: 'Text', text: /^✻$/ })).toBeDefined()

  await $.tool.call({
    tool: UPDATE,
    version_hash: 'h1',
    scope: SCOPE,
    ref: 't1',
    status: 'need_review',
  })
  expect((await ui.find({ type: 'Text', text: /^à relire$/ }))?.text).toBe('à relire')

  await $.tool.call({
    tool: CREATE,
    version_hash: 'h1',
    scope: SCOPE,
    type: 'task',
    title: 'nouvelle tâche',
    planId: 'p1',
  })
  expect((await ui.find({ type: 'Text', text: /nouvelle tâche/ }))?.text).toBe('nouvelle tâche')
  await ui.unmount()
})

test('Rafraîchir rereads the active view by the server’s own call; Backlog reads and hides the backlog', async ($, on) => {
  const pages: Pages = { first: [PLAN, TASK], backlog: [LATER] }
  const { reads } = world(on, pages)
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  pages.first = [ORPHAN]
  await ui.press({ key: 'refresh' })
  expect(reads).toHaveLength(1)
  expect(reads[0]).toMatchObject({
    server: SERVER,
    tool: 'list_items',
    version_hash: 'h1',
    scope: SCOPE,
    view: 'active',
  })
  expect(await titles(ui)).toEqual([ORPHAN.title])

  await ui.press({ key: 'backlog' })
  expect(reads[1]).toMatchObject({ tool: 'list_items', scope: SCOPE, view: 'backlog' })
  expect(await titles(ui)).toEqual([ORPHAN.title, LATER.title])
  expect((await ui.find({ type: 'Text', text: /^backlog$/ }))?.text).toBe('backlog')
  expect((await ui.find({ type: 'Button', key: 'backlog' }))?.text).toBe('Masquer le backlog')

  await ui.press({ key: 'backlog' })
  expect(await titles(ui)).toEqual([ORPHAN.title])
  expect(reads).toHaveLength(2)
  await ui.unmount()
})

test('a server call that rejects says so in a toast and frees the buttons', async ($, on) => {
  const { reads, toasts, outage } = world(on, { first: [PLAN, TASK] })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  outage.message = 'no server named plugin_nestor_nestor'
  await ui.press({ key: 'refresh' })
  expect(toasts).toHaveLength(1)
  expect(toasts[0]).toMatch(/^Nestor : list_items injoignable sur plugin_nestor_nestor · /)
  expect(await titles(ui)).toEqual([PLAN.title, TASK.title])

  await ui.press({ key: 'row:t1' })
  await ui.press({ key: 'detail:t1' })
  expect(toasts[1]).toMatch(/^Nestor : get_item injoignable sur plugin_nestor_nestor · /)
  expect((await ui.find({ type: 'Button', key: 'detail:t1' }))?.text).toBe('Lire le détail')

  outage.message = null
  await ui.press({ key: 'refresh' })
  expect(reads).toHaveLength(3)
  expect(toasts).toHaveLength(2)
  await ui.unmount()
})

test('/nestor-taches toggles the pane; with a project name it reads that project', async ($, on) => {
  const { reads, opened, closed, panes } = world(on, { first: [ORPHAN] })
  await $.session.start(STARTED)

  expect(await $.command.run({ ...RUN, args: '' })).toEqual({
    text: 'Panneau Nestor ouvert.',
  })
  expect(opened).toEqual(['Nestor · tâches'])
  panes.push({
    id: 'nestor-taches',
    title: 'Nestor · tâches',
    isShown: true,
    isFocused: false,
    isPlaced: true,
  })
  expect(await $.command.run({ ...RUN, args: '' })).toEqual({
    text: 'Panneau Nestor fermé.',
  })
  expect(closed).toEqual(['nestor-taches'])

  expect(await $.command.run({ ...RUN, args: 'Skyline' })).toEqual({
    text: 'Panneau Nestor ouvert sur Skyline.',
  })
  expect(reads[0]).toMatchObject({ server: SERVER, tool: 'get_project', name: 'Skyline' })
  expect(String(reads[0]?.version_hash)).toMatch(NESTOR_BETA_HASH)
  expect(reads[1]).toMatchObject({ tool: 'list_items', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await titles(ui)).toEqual([ORPHAN.title])
  await ui.unmount()

  expect(await $.command.run({ ...RUN, args: 'Nulle part' })).toEqual({
    text: 'Nestor : aucun projet ne correspond à « Nulle part ».',
  })
})

test('without a read, the pane says what to run', async ($, on) => {
  world(on, { first: [] })
  await $.session.start(STARTED)

  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /next-tasks/ }))?.text).toBe(
    "Lance /nestor-beta:next-tasks, ou /nestor-taches suivi d'un nom de projet.",
  )
  await ui.unmount()
})

const GET = 'mcp__plugin_nestor_nestor__get_item'

const rows = async (ui: { findAll: (q: { type: string }) => Promise<{ key?: string }[]> }) =>
  (await ui.findAll({ type: 'Button' }))
    .map(one => one.key)
    .filter(key => key?.startsWith('row:'))

test('/nestor-taches X says the read failed when the server does not answer, never that no project matches', async ($, on) => {
  const { outage } = world(on, { first: [ORPHAN] })
  await $.session.start(STARTED)

  outage.message = 'ECONNREFUSED'
  const unreachable = await $.command.run({ ...RUN, args: 'Skyline' })
  expect(unreachable.text).toMatch(/impossible/)
  expect(unreachable.text).not.toMatch(/aucun projet/)

  outage.tools = ['list_items']
  const unread = await $.command.run({ ...RUN, args: 'Skyline' })
  expect(unread.text).toMatch(/impossible/)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /lu à/ })).toBeUndefined()
  await ui.unmount()
})

test('a filtered, sorted, limited, versions-only or foreign-cursor read by Claude leaves the pane’s view as it is', async ($, on) => {
  const FOREIGN = { ...ORPHAN, id: 'zz9', project: { id: 'OTHR', name: 'Autre' } }
  const GLOBAL_COUNTS = { taskViewCounts: { ...COUNTS, active: 57, backlog: 12 } }
  world(on, { first: [PLAN, TASK, ORPHAN] }, undefined, {
    tool: call =>
      call.projection === 'versions'
        ? pageOf([{ id: 'p1', version: 3 }])
        : call.sort !== undefined || call.filters !== undefined
          ? pageOf([ORPHAN], { hasMore: true, nextCursor: 'cX' })
          : (call.scope as Call | undefined)?.mode === 'global'
            ? pageOf([ORPHAN], { hasMore: true, nextCursor: 'g2', ...GLOBAL_COUNTS })
            : call.cursor === 'g2' || call.cursor === 'cX'
              ? pageOf([FOREIGN], GLOBAL_COUNTS)
              : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  const before = await rows(ui)

  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active', sort: 'updated_desc', limit: 10 })
  await $.tool.call({ tool: LIST, version_hash: 'h1', cursor: 'cX' })
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active', filters: { types: ['task'] } })
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active', projection: 'versions' })
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: { mode: 'global' }, view: 'active' })
  await $.tool.call({ tool: LIST, version_hash: 'h1', cursor: 'g2' })

  expect(before).toEqual(['row:p1', 'row:t1', 'row:t2'])
  expect(await rows(ui)).toEqual(before)
  expect((await ui.find({ type: 'Text', text: /actives/ }))?.text).toMatch(/^3 actives · 1 en backlog/)
  await ui.unmount()
})

test('Rafraîchir keeps the ancestor read outside the view above its subtask', async ($, on) => {
  const SUB = { ...ORPHAN, id: 't9', title: 'sous-tâche', parentTaskId: 'tP' }
  const PARENT = { id: 'tP', type: 'task', title: 'tâche parente', status: 'completed', priority: 'normal', backlog: false, version: 4 }
  world(on, { first: [SUB] }, undefined, {
    tool: call =>
      call.tool === GET
        ? { results: [{ ref: 'tP', item: PARENT, project: SKYLINE, tags: [], relations: [], etag: 'e' }] }
        : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  await $.tool.call({ tool: GET, version_hash: 'h1', scope: SCOPE, ref: ['tP'], known: [null] })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await rows(ui)).toEqual(['row:tP', 'row:t9'])

  await ui.press({ key: 'refresh' })
  expect(await rows(ui)).toEqual(['row:tP', 'row:t9'])
  await ui.press({ key: 'row:t9' })
  expect(await ui.find({ type: 'Text', text: /parent non lu/ })).toBeUndefined()
  await ui.unmount()
})

test('a get_item answer that keeps the content unchanged keeps the detail already read', async ($, on) => {
  const { body: _body, specification: _spec, ...meta } = READ.item
  world(on, { first: [PLAN, TASK] }, undefined, {
    tool: call =>
      call.tool === GET && call.known !== null
        ? { contentUnchanged: true, item: meta, project: SKYLINE, tags: [], relations: [], etag: 'e9', contentEtag: 'c1' }
        : call.tool === GET
          ? READ
          : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  await $.tool.call({ tool: GET, version_hash: 'h1', scope: SCOPE, ref: 't1', known: null })
  await $.tool.call({ tool: GET, version_hash: 'h1', scope: SCOPE, ref: 't1', known: { version: 1, etag: 'e1', contentEtag: 'c1' } })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'row:t1' })
  expect((await ui.find({ type: 'Markdown', text: /Corps de la tâche/ }))?.text).toContain('### Spécification')
  expect(await ui.find({ type: 'Text', text: /aucun contenu/ })).toBeUndefined()
  await ui.unmount()
})

test('an update_item patch moves the row: new title and priority, out of the list once in the backlog or the trash', async ($, on) => {
  const answer = (call: Call) => ({
    item: { id: call.id, type: 'task', version: 2, status: 'todo', slug: 'amber_koala' },
    etag: 'e2',
  })
  world(on, { first: [PLAN, TASK, ORPHAN, NOTE] }, undefined, {
    tool: call => (call.tool === UPDATE ? answer(call) : undefined),
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  await $.tool.call({
    tool: UPDATE,
    version_hash: 'h1',
    scope: SCOPE,
    id: 't2',
    operation: 'patch',
    patch: { title: 'corriger la connexion', priority: 'urgent', dueAt: null },
    expectedVersion: 1,
    expectedEtag: 'e1',
  })
  expect((await ui.find({ type: 'Button', key: 'row:t2' }))?.text).toBe(
    '○ corriger la connexion · à faire · ↑↑ urgente',
  )

  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 't2', operation: 'patch', patch: { backlog: true } })
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 'n2', operation: 'patch', patch: { trashed: true } })
  expect(await rows(ui)).toEqual(['row:p1', 'row:t1'])
  await ui.unmount()
})

test('a plan’s detail draws its own specification', async ($, on) => {
  const SPEC = {
    objective: 'Découper le monolithe',
    requirements: ['API stable'],
    architecture: 'Hexagonale',
    verificationPlan: ['e2e verts'],
  }
  world(on, { first: [PLAN, TASK] }, undefined, {
    mcp: (tool, args) =>
      tool === 'get_item' && args.ref === 'p1'
        ? { item: { ...PLAN, specification: SPEC }, project: SKYLINE, tags: [], relations: [], etag: 'e1' }
        : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  await ui.press({ key: 'row:p1' })
  await ui.press({ key: 'detail:p1' })

  const text = (await ui.find({ type: 'Markdown' }))?.text ?? ''
  for (const part of [SPEC.objective, 'API stable', SPEC.architecture, 'e2e verts']) {
    expect(text).toContain(part)
  }
  await ui.unmount()
})

test('a plan created after the tasks joins the one Plans section', async ($, on) => {
  world(on, { first: [PLAN, TASK, ORPHAN] }, undefined, {
    tool: call =>
      call.tool === CREATE ? { item: { id: 'p7', type: 'plan', version: 1, slug: 'new_plan' }, etag: 'e3' } : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  await $.tool.call({ tool: CREATE, version_hash: 'h1', scope: SCOPE, type: 'plan', title: 'nouveau plan' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.findAll({ type: 'Text', text: /^(Plans|Tâches)$/ })).map(one => one.text)).toEqual([
    'Plans',
    'Tâches',
  ])
  expect(await rows(ui)).toEqual(['row:p1', 'row:t1', 'row:p7', 'row:t2'])
  await ui.unmount()
})

test('a task sent to the hidden backlog and brought back returns to the list', async ($, on) => {
  const pages: Pages = { first: [PLAN, TASK, ORPHAN] }
  world(on, pages, undefined, {
    tool: call =>
      call.tool === UPDATE
        ? { item: { id: call.id, type: 'task', version: 2, status: 'todo', slug: 'amber_koala' }, etag: 'e2' }
        : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  pages.first = [PLAN, TASK]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 't2', operation: 'patch', patch: { backlog: true } })
  expect(await rows(ui)).toEqual(['row:p1', 'row:t1'])

  pages.first = [PLAN, TASK, ORPHAN]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 't2', operation: 'patch', patch: { backlog: false } })
  expect(await rows(ui)).toEqual(['row:p1', 'row:t1', 'row:t2'])
  await ui.unmount()
})

test('Rafraîchir keeps an ancestor whose subtask comes on a later page', async ($, on) => {
  const SUB = { ...ORPHAN, id: 't9', title: 'sous-tâche', parentTaskId: 'tP' }
  const PARENT = { id: 'tP', type: 'task', title: 'tâche parente', status: 'completed', priority: 'normal', backlog: false, version: 4 }
  world(on, { first: [TASK], next: [SUB] }, undefined, {
    tool: call =>
      call.tool === GET
        ? { results: [{ ref: 'tP', item: PARENT, project: SKYLINE, tags: [], relations: [], etag: 'e' }] }
        : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  await $.tool.call({ tool: LIST, version_hash: 'h1', cursor: 'c1' })
  await $.tool.call({ tool: GET, version_hash: 'h1', scope: SCOPE, ref: ['tP'], known: [null] })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tP', 'row:t9'])

  await ui.press({ key: 'refresh' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tP', 'row:t9'])
  await ui.unmount()
})

test('a task brought back from the hidden backlog in global scope returns to the list', async ($, on) => {
  const pages: Pages = { first: [PLAN, TASK, ORPHAN] }
  world(on, pages, undefined, {
    tool: call =>
      call.tool === UPDATE
        ? { item: { id: call.id, type: 'task', version: 2, status: 'todo', slug: 'amber_koala' }, etag: 'e2' }
        : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  const GLOBAL = { mode: 'global' }

  pages.first = [PLAN, TASK]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: GLOBAL, id: 't2', operation: 'patch', patch: { backlog: true } })
  expect(await rows(ui)).toEqual(['row:p1', 'row:t1'])

  pages.first = [PLAN, TASK, ORPHAN]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: GLOBAL, id: 't2', operation: 'patch', patch: { backlog: false } })
  expect(await rows(ui)).toEqual(['row:p1', 'row:t1', 'row:t2'])
  await ui.unmount()
})

test('a subtask that goes through the backlog comes back under its ancestor read outside the view', async ($, on) => {
  const SUB = { ...ORPHAN, id: 't9', title: 'sous-tâche', parentTaskId: 'tP' }
  const PARENT = { id: 'tP', type: 'task', title: 'tâche parente', status: 'completed', priority: 'normal', backlog: false, version: 4 }
  const pages: Pages = { first: [TASK, SUB] }
  world(on, pages, undefined, {
    tool: call =>
      call.tool === GET
        ? { results: [{ ref: 'tP', item: PARENT, project: SKYLINE, tags: [], relations: [], etag: 'e' }] }
        : call.tool === UPDATE
          ? { item: { id: call.id, type: 'task', version: 2, status: 'todo', slug: 'amber_koala' }, etag: 'e2' }
          : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  await $.tool.call({ tool: GET, version_hash: 'h1', scope: SCOPE, ref: ['tP'], known: [null] })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tP', 'row:t9'])

  pages.first = [TASK]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 't9', operation: 'patch', patch: { backlog: true } })
  expect(await rows(ui)).toEqual(['row:t1'])

  pages.first = [TASK, SUB]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 't9', operation: 'patch', patch: { backlog: false } })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tP', 'row:t9'])
  await ui.press({ key: 'refresh' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tP', 'row:t9'])
  await ui.unmount()
})

test('a parent sent to the hidden backlog stays above its active subtask, through Rafraîchir too', async ($, on) => {
  const PARENT = { ...ORPHAN, id: 'tA', title: 'préparer la livraison' }
  const CHILD = { ...ORPHAN, id: 't9', title: 'vérifier les tests', parentTaskId: 'tA' }
  const pages: Pages = { first: [TASK, PARENT, CHILD] }
  world(on, pages, undefined, {
    tool: call =>
      call.tool === UPDATE
        ? { item: { id: call.id, type: 'task', version: 2, status: 'todo', slug: 'amber_koala' }, etag: 'e2' }
        : undefined,
  })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tA', 'row:t9'])

  pages.first = [TASK, CHILD]
  await $.tool.call({ tool: UPDATE, version_hash: 'h1', scope: SCOPE, id: 'tA', operation: 'patch', patch: { backlog: true } })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tA', 'row:t9'])
  expect(await ui.find({ type: 'Text', text: /^hors vue$/ })).toBeDefined()

  await ui.press({ key: 'refresh' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tA', 'row:t9'])
  await ui.unmount()
})

test('hiding the backlog keeps a backlog parent above its active subtask', async ($, on) => {
  const PARENT = { ...LATER, id: 'tB', title: 'chantier en attente' }
  const CHILD = { ...ORPHAN, id: 't9', title: 'vérifier les tests', parentTaskId: 'tB' }
  world(on, { first: [TASK, CHILD], backlog: [PARENT] })
  await $.session.start(STARTED)
  await $.tool.call({ tool: LIST, version_hash: 'h1', scope: SCOPE, view: 'active' })
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })

  await ui.press({ key: 'backlog' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tB', 'row:t9'])
  await ui.press({ key: 'backlog' })
  expect(await rows(ui)).toEqual(['row:t1', 'row:tB', 'row:t9'])
  await ui.unmount()
})
