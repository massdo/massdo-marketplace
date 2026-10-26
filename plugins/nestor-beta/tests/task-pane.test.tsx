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

// The engine beneath the mod: a Nestor server answering from memory, and what the mod opens, closes and submits.
const world = (on: On, pages: Pages, tools = [{ name: LIST, description: '', mcp: true }]) => {
  const calls: Call[] = []
  const reads: Call[] = []
  const opened: string[] = []
  const closed: string[] = []
  const submitted: Call[] = []
  const toasts: string[] = []
  // Set to a message, every $.mcp.call rejects with it, as an unreachable server does.
  const outage: { message: string | null } = { message: null }
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
    const payload = e.tool.endsWith('__list_items')
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
          : {}
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
    if (outage.message !== null) {
      throw new Error(outage.message)
    }
    const payload =
      e.tool === 'get_item'
        ? READ
        : e.tool === 'list_items'
          ? listPage(args)
          : e.tool === 'get_project'
            ? args.name === 'Skyline'
              ? { ...SKYLINE, normalizedName: 'skyline', version: 1 }
              : null
            : e.tool === 'search_project'
              ? { items: [], totalCount: 0, hasMore: false }
              : {}
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
  expect(reads[0]).toMatchObject({
    server: SERVER,
    tool: 'get_project',
    version_hash: 'unknown',
    name: 'Skyline',
  })
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
