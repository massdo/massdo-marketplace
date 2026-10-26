import { atom, read, update } from 'claude-code'
import type { Color, EngineInterface, Register } from 'claude-code'

import type {
  NestorBusy,
  NestorCounts,
  NestorDate,
  NestorDetail,
  NestorEntry,
  NestorItem,
  NestorPlan,
  NestorPriority,
  NestorProgress,
  NestorProject,
  NestorSource,
  NestorTask,
  NestorTaskStatus,
} from '../types'

const PANE = 'nestor-taches'
const COMMAND = 'nestor-taches'
const NESTOR_TOOL =
  /^mcp__(.+)__(list_items|get_item|get_project|update_item|create_item|manage_build)$/i
const NESTOR_LIST = /^mcp__(.+)__list_items$/i

const project = atom(
  { plugin: 'nestor-beta', key: 'project' } as const,
  null as NestorProject | null,
)
const items = atom({ plugin: 'nestor-beta', key: 'items' } as const, [] as NestorEntry[])
const details = atom(
  { plugin: 'nestor-beta', key: 'details' } as const,
  {} as Record<string, NestorDetail>,
)
const expanded = atom(
  { plugin: 'nestor-beta', key: 'expanded' } as const,
  {} as Record<string, true>,
)
const counts = atom({ plugin: 'nestor-beta', key: 'counts' } as const, null as NestorCounts | null)
const source = atom({ plugin: 'nestor-beta', key: 'source' } as const, null as NestorSource | null)
const readAt = atom({ plugin: 'nestor-beta', key: 'readAt' } as const, null as number | null)
const showBacklog = atom({ plugin: 'nestor-beta', key: 'showBacklog' } as const, false)
const busy = atom({ plugin: 'nestor-beta', key: 'busy' } as const, null as NestorBusy | null)

/** Colors are theme keys, so the pane follows the light or dark theme; null is drawn dim. */
type Mark = { glyph: string; label: string; color: Color | null }
type Part = { text: string; color: Color | null }

const STATUS: Record<NestorTaskStatus, Mark> = {
  todo: { glyph: '○', label: 'à faire', color: null },
  ready_to_build: { glyph: '●', label: 'prête à build', color: 'claude' },
  building: { glyph: '✻', label: 'build en cours', color: 'text' },
  in_progress: { glyph: '◐', label: 'en cours', color: 'text' },
  need_review: { glyph: '◉', label: 'à relire', color: 'text' },
  completed: { glyph: '✓', label: 'terminée', color: null },
  cancelled: { glyph: '×', label: 'annulée', color: null },
}

const PROGRESS: Record<NestorProgress, Mark> = {
  not_started: { glyph: '○', label: 'non démarré', color: null },
  in_progress: { glyph: '◐', label: 'en cours', color: 'text' },
  blocked: { glyph: '⊘', label: 'bloqué', color: 'error' },
  completed: { glyph: '✓', label: 'terminé', color: null },
}

const PRIORITY: Record<NestorPriority, Part | null> = {
  low: { text: '↓ basse', color: null },
  normal: null,
  high: { text: '↑ haute', color: null },
  urgent: { text: '↑↑ urgente', color: 'error' },
}

const tint = (color: Color | null) => (color === null ? { dimColor: true } : { color })

const MONTHS = [
  'janv.',
  'févr.',
  'mars',
  'avr.',
  'mai',
  'juin',
  'juil.',
  'août',
  'sept.',
  'oct.',
  'nov.',
  'déc.',
]

type Loose = Record<string, unknown>

const isRecord = (value: unknown): value is Loose =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const isItem = (value: unknown): value is NestorItem =>
  isRecord(value) &&
  typeof value.id === 'string' &&
  (value.type === 'task' || value.type === 'plan' || value.type === 'note')

const isBacklog = (one: NestorEntry) => one.type === 'task' && one.backlog

const isApproved = (one: NestorTask | NestorPlan) =>
  one.approval !== undefined &&
  one.workRevision !== undefined &&
  one.approval.workRevision === one.workRevision

function parentOf(one: NestorEntry): string | undefined {
  if (one.type === 'task') {
    return one.planId ?? one.parentTaskId
  }
  if (one.type === 'plan') {
    return one.parentPlanId
  }

  return undefined
}

function markOf(one: NestorEntry): Mark {
  if (one.type === 'task') {
    return STATUS[one.status] ?? { glyph: '?', label: one.status, color: null }
  }
  if (one.type === 'plan') {
    const mark = one.progress === undefined ? undefined : PROGRESS[one.progress]

    return mark ?? { glyph: '○', label: '', color: null }
  }

  return { glyph: '¶', label: 'note', color: null }
}

/** The quiet line under a title; only an overdue date, an urgent priority or a blocked plan stands out. */
function metaOf(one: NestorEntry, now: number): Part[] {
  const dim = (text: string): Part => ({ text, color: null })
  const parts: Part[] = []
  if (one.type === 'task') {
    parts.push(dim(markOf(one).label))
    const priority = PRIORITY[one.priority]
    if (priority) {
      parts.push(priority)
    }
    if (one.dueAt) {
      const date = shortDate(one.dueAt)
      parts.push(
        isPast(one.dueAt, now)
          ? { text: `en retard, échéance ${date}`, color: 'error' }
          : dim(`échéance ${date}`),
      )
    } else if (one.scheduledAt) {
      parts.push(dim(`prévue le ${shortDate(one.scheduledAt)}`))
    }
    if (one.backlog) {
      parts.push(dim('backlog'))
    }
  } else if (one.type === 'plan') {
    parts.push(dim(one.parentPlanId === undefined ? 'plan' : 'sous-plan'))
    const { label } = markOf(one)
    if (label !== '') {
      parts.push({ text: label, color: one.progress === 'blocked' ? 'error' : null })
    }
  } else {
    parts.push(dim('note'))
  }
  if (one.isContext) {
    parts.push(dim('hors vue'))
  }

  return parts
}

const titleOf = (one: NestorEntry) => one.title ?? one.slug ?? one.id

const pad = (n: number) => String(n).padStart(2, '0')

function dayOf(one: NestorDate): Date | null {
  const at = new Date('date' in one ? `${one.date}T00:00:00` : one.instant)

  return Number.isNaN(at.getTime()) ? null : at
}

function shortDate(one: NestorDate): string {
  const at = dayOf(one)
  if (at === null) {
    return 'date' in one ? one.date : one.instant
  }
  const day = `${at.getDate()} ${MONTHS[at.getMonth()] ?? ''}`

  return 'date' in one ? day : `${day} ${pad(at.getHours())}:${pad(at.getMinutes())}`
}

function isPast(one: NestorDate, now: number): boolean {
  const at = dayOf(one)
  if (at === null) {
    return false
  }
  if ('date' in one) {
    at.setHours(23, 59, 59, 999)
  }

  return at.getTime() < now
}

const timeText = (at: number) => {
  const date = new Date(at)

  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function approvalText(one: NestorEntry): string | null {
  if (one.type === 'note') {
    return null
  }
  if (!one.approval) {
    return 'aucune approbation'
  }

  return isApproved(one)
    ? 'approbation courante'
    : `approbation ancienne (révision ${one.approval.workRevision})`
}

function specificationText(detail: NestorDetail): string {
  const spec = detail.specification
  if (!spec) {
    return ''
  }
  const lines: string[] = ['', '### Spécification']
  if (spec.context) {
    lines.push('', spec.context)
  }
  if (spec.steps?.length) {
    lines.push('', '**Étapes**')
    spec.steps.forEach((step, index) => {
      const check = step.verification ? ` — vérification : ${step.verification}` : ''
      lines.push(`${index + 1}. ${step.action ?? ''}${check}`)
    })
  }
  if (spec.doneWhen?.length) {
    lines.push('', '**Terminé quand**')
    for (const rule of spec.doneWhen) {
      lines.push(`- ${rule}`)
    }
  }
  if (spec.repository) {
    lines.push('', `Dépôt : ${spec.repository}`)
  }

  return lines.join('\n')
}

function parseJson(text: string): Loose | null {
  try {
    const parsed: unknown = JSON.parse(text)

    return isRecord(parsed) ? parsed : null
  } catch {
    return null
  }
}

/** The structured result of a Nestor call, as core or the MCP SDK hands it: structuredContent, else its JSON text. */
function payloadOf(ran: { result?: unknown; text?: string }): Loose | null {
  const result = ran.result
  if (isRecord(result)) {
    if (isRecord(result.structuredContent)) {
      return result.structuredContent
    }
    if (Array.isArray(result.content)) {
      for (const block of result.content) {
        const parsed =
          isRecord(block) && typeof block.text === 'string' ? parseJson(block.text) : null
        if (parsed) {
          return parsed
        }
      }
    }
  }

  return typeof ran.text === 'string' ? parseJson(ran.text) : null
}

function errorText(ran: { content: { text?: string }[] }): string {
  const text = ran.content.find(block => typeof block.text === 'string')?.text ?? 'erreur inconnue'

  return text.length > 160 ? `${text.slice(0, 159)}…` : text
}

async function setBusy($: EngineInterface, value: NestorBusy | null) {
  await update($, busy, () => value)
}

/** One page of an active or backlog read: a fresh read replaces that view, a cursor page adds to it. */
async function absorbPage($: EngineInterface, server: string, call: Loose, page: Loose) {
  const fresh = Array.isArray(page.items) ? page.items.filter(isItem) : null
  const view = typeof page.view === 'string' ? page.view : call.view
  if (fresh === null || (view !== 'active' && view !== 'backlog')) {
    return
  }
  const isNewRead = typeof call.cursor !== 'string'
  const scope = isRecord(call.scope) ? call.scope : null
  const projectId = scope && typeof scope.projectId === 'string' ? scope.projectId : null
  const known = await read($, project)
  if (isNewRead && projectId === null) {
    return
  }
  const isNewProject = projectId !== null && projectId !== known?.id
  if (isNewProject) {
    const named = fresh.find(one => one.project?.id === projectId)?.project
    await update($, project, () => ({ id: projectId, name: named?.name ?? projectId }))
    await update($, details, () => ({}))
    await update($, expanded, () => ({}))
    await update($, showBacklog, () => false)
  }
  await update($, items, all => {
    const kept = isNewProject
      ? []
      : !isNewRead
        ? all
        : all.filter(one => (view === 'backlog' ? !isBacklog(one) : isBacklog(one)))
    const merged = kept.map(one => fresh.find(next => next.id === one.id) ?? one)
    const ids = new Set(merged.map(one => one.id))

    return [...merged, ...fresh.filter(one => !ids.has(one.id))]
  })
  if (view === 'backlog') {
    await update($, showBacklog, () => true)
  }
  const totals = isRecord(page.taskViewCounts) ? page.taskViewCounts : null
  if (totals && typeof totals.active === 'number' && typeof totals.backlog === 'number') {
    const next: NestorCounts = { active: totals.active, backlog: totals.backlog }
    await update($, counts, () => next)
  }
  if (typeof call.version_hash === 'string') {
    const next: NestorSource = { server, versionHash: call.version_hash }
    await update($, source, () => next)
  }
  await update($, readAt, () => Date.now())
  const named = await read($, project)
  const total = await read($, counts)
  $.ui.status(`Nestor · ${named?.name ?? '?'} · ${total?.active ?? '?'} actives`)
  void $.ui.open({ id: PANE, title: `Nestor · ${named?.name ?? 'tâches'}` })
}

/** One item read in full: its detail, and its row when a listed item names it as parent. */
async function absorbItem($: EngineInterface, item: NestorItem & Loose) {
  const detail: NestorDetail = { readAt: Date.now() }
  if (typeof item.body === 'string') {
    detail.body = item.body
  }
  if (isRecord(item.specification)) {
    detail.specification = item.specification
  }
  await update($, details, all => ({ ...all, [item.id]: detail }))
  const { body: _body, specification: _spec, ...compact } = item
  await update($, items, all => {
    if (all.some(one => one.id === item.id)) {
      return all.map(one =>
        one.id === item.id ? ({ ...one, ...compact, type: one.type } as NestorEntry) : one,
      )
    }
    const isNamed = all.some(one => parentOf(one) === item.id)

    return isNamed ? [...all, { ...(compact as NestorItem), isContext: true as const }] : all
  })
}

async function absorbRead($: EngineInterface, page: Loose) {
  const entries = Array.isArray(page.results) ? page.results : [page]
  for (const entry of entries) {
    if (isRecord(entry) && isItem(entry.item)) {
      await absorbItem($, entry.item as NestorItem & Loose)
    }
  }
}

async function absorbProject($: EngineInterface, page: Loose) {
  if (typeof page.id === 'string' && typeof page.name === 'string') {
    const named: NestorProject = { id: page.id, name: page.name }
    await update($, project, known => (known?.id === named.id ? named : (known ?? named)))
  }
}

/** A mutation Claude made: the listed row follows it, and a task or plan created in the project joins the list. */
async function absorbMutation($: EngineInterface, name: string, call: Loose, page: Loose) {
  const item = isRecord(page.item) ? page.item : null
  if (item === null || typeof item.id !== 'string') {
    return
  }
  const id = item.id
  const status = typeof item.status === 'string' ? (item.status as NestorTaskStatus) : undefined
  const slug = typeof item.slug === 'string' ? item.slug : undefined
  const all = await read($, items)
  if (all.some(one => one.id === id)) {
    await update($, items, list =>
      list.map(one => {
        if (one.id !== id) {
          return one
        }
        const next = { ...one, ...(slug === undefined ? {} : { slug }) }

        return (
          one.type === 'task' && status !== undefined ? { ...next, status } : next
        ) as NestorEntry
      }),
    )
    await update($, details, list => {
      const { [id]: _stale, ...rest } = list

      return rest
    })

    return
  }
  if (name !== 'create_item') {
    return
  }
  const named = await read($, project)
  const scope = isRecord(call.scope) ? call.scope : null
  const title = typeof call.title === 'string' ? call.title : null
  if (named === null || scope?.projectId !== named.id || title === null) {
    return
  }
  const parent = (key: string) =>
    typeof call[key] === 'string' ? (call[key] as string) : undefined
  let entry: NestorEntry | null = null
  if (item.type === 'task') {
    const priority =
      typeof call.priority === 'string' ? (call.priority as NestorPriority) : 'normal'
    const backlog = call.backlog === true
    if (backlog && !(await read($, showBacklog))) {
      return
    }
    entry = {
      id,
      type: 'task',
      title,
      slug,
      status: status ?? 'todo',
      priority,
      backlog,
      planId: parent('planId'),
      parentTaskId: parent('parentTaskId'),
      ...(call.template === 'code' ? { template: 'code' as const } : {}),
    }
  } else if (item.type === 'plan') {
    entry = { id, type: 'plan', title, slug, parentPlanId: parent('parentPlanId') }
  }
  if (entry !== null) {
    const added = entry
    await update($, items, list => [...list, added])
  }
}

/** Nestor under any server name: the desktop host lists it by a connector id, so the call's own `version_hash` tells it apart. */
function nestorCall(tool: string, input: Loose): { server: string; name: string } | null {
  const match = NESTOR_TOOL.exec(tool)
  if (match === null) {
    return null
  }
  const [, server = '', name = ''] = match
  if (!/nestor/i.test(server) && typeof input.version_hash !== 'string') {
    return null
  }

  return { server, name }
}

async function resolveSource($: EngineInterface): Promise<NestorSource | null> {
  const held = await read($, source)
  if (held !== null) {
    return held
  }
  const tools = await $.tool.list()
  for (const tool of tools) {
    const server = NESTOR_LIST.exec(tool.name)?.[1]
    if (server !== undefined && /nestor|journal/i.test(`${server} ${tool.description}`)) {
      const found: NestorSource = { server, versionHash: 'unknown' }
      await update($, source, () => found)

      return found
    }
  }

  return null
}

/** The pane's own call to the Nestor server: no permission dialog, nothing in the transcript. */
async function callNestor(
  $: EngineInterface,
  tool: string,
  args: Loose,
  options: { isQuiet?: true } = {},
): Promise<Loose | null> {
  const src = await resolveSource($)
  if (src === null) {
    $.ui.toast('Nestor : aucun serveur Nestor dans cette session')

    return null
  }
  const ran = await $.mcp.call(src.server, tool, { version_hash: src.versionHash, ...args })
  if (ran.isError) {
    if (!options.isQuiet) {
      $.ui.toast(`Nestor : ${tool} refusé · ${errorText(ran)}`)
    }

    return null
  }
  const page = payloadOf({ result: ran })
  if (page === null && !options.isQuiet) {
    $.ui.toast(`Nestor : réponse de ${tool} illisible`)
  }

  return page
}

async function readView($: EngineInterface, view: 'active' | 'backlog') {
  const named = await read($, project)
  if (named === null) {
    return
  }
  const scope = { mode: 'project', projectId: named.id }
  let cursor: string | undefined
  do {
    const args: Loose = cursor === undefined ? { scope, view } : { cursor }
    const page = await callNestor($, 'list_items', args)
    if (page === null) {
      return
    }
    const src = await read($, source)
    await absorbPage($, src?.server ?? '', { ...args, view, version_hash: src?.versionHash }, page)
    cursor =
      page.hasMore === true && typeof page.nextCursor === 'string' ? page.nextCursor : undefined
  } while (cursor !== undefined)
}

async function refresh($: EngineInterface) {
  if ((await read($, busy)) !== null) {
    return
  }
  await setBusy($, 'refresh')
  try {
    await readView($, 'active')
    if (await read($, showBacklog)) {
      await readView($, 'backlog')
    }
  } finally {
    await setBusy($, null)
  }
}

async function toggleBacklog($: EngineInterface) {
  if ((await read($, busy)) !== null) {
    return
  }
  if (await read($, showBacklog)) {
    await update($, items, all => all.filter(one => !isBacklog(one)))
    await update($, showBacklog, () => false)

    return
  }
  await setBusy($, 'backlog')
  try {
    await readView($, 'backlog')
  } finally {
    await setBusy($, null)
  }
}

async function fetchDetail($: EngineInterface, id: string) {
  const named = await read($, project)
  if (named === null || (await read($, busy)) !== null) {
    return
  }
  await setBusy($, { detail: id })
  try {
    const page = await callNestor($, 'get_item', {
      scope: { mode: 'project', projectId: named.id },
      ref: id,
      known: null,
    })
    if (page !== null) {
      await absorbRead($, page)
    }
  } finally {
    await setBusy($, null)
  }
}

/** Reads one project by its exact name, else by a search that yields a single project. */
async function openProject($: EngineInterface, name: string): Promise<{ text: string }> {
  if ((await read($, busy)) !== null) {
    return { text: 'Nestor : une lecture est déjà en cours.' }
  }
  await setBusy($, 'project')
  try {
    let found = await callNestor($, 'get_project', { name }, { isQuiet: true })
    if (found === null || typeof found.id !== 'string' || typeof found.name !== 'string') {
      const search = await callNestor($, 'search_project', { query: name })
      const candidates = search && Array.isArray(search.items) ? search.items.filter(isRecord) : []
      const names = candidates.map(one => String(one.name ?? one.id))
      if (candidates.length === 0) {
        return { text: `Nestor : aucun projet ne correspond à « ${name} ».` }
      }
      if (candidates.length > 1 || search?.hasMore === true) {
        return {
          text: `Nestor : plusieurs projets correspondent à « ${name} » : ${names.join(', ')}.`,
        }
      }
      found = candidates[0] ?? null
    }
    if (found === null || typeof found.id !== 'string' || typeof found.name !== 'string') {
      return { text: `Nestor : projet « ${name} » illisible.` }
    }
    const named: NestorProject = { id: found.id, name: found.name }
    await update($, project, () => named)
    await update($, items, () => [])
    await update($, details, () => ({}))
    await update($, expanded, () => ({}))
    await update($, counts, () => null)
    await update($, showBacklog, () => false)
    await readView($, 'active')
    await $.ui.open({ id: PANE, title: `Nestor · ${named.name}` })

    return { text: `Panneau Nestor ouvert sur ${named.name}.` }
  } finally {
    await setBusy($, null)
  }
}

/** The click is the person's own invocation of the skill: the command runs as if typed at the prompt. */
async function submitSkill($: EngineInterface, skill: 'spec' | 'build', one: NestorEntry) {
  const ref = one.slug ?? one.id
  const named = await read($, project)
  const scope = skill === 'spec' && named !== null ? ` project:${named.id}` : ''
  try {
    const ran = await $.command.run({ command: `nestor-beta:${skill}`, args: `${ref}${scope}` })
    const denied = (ran as { deny?: string }).deny
    if (typeof denied === 'string') {
      $.ui.toast(`Nestor : ${skill} refusé · ${denied}`)
    }
  } catch (error) {
    $.ui.toast(
      `Nestor : ${skill} refusé · ${error instanceof Error ? error.message : String(error)}`,
    )
  }
}

function toggle($: EngineInterface, id: string) {
  return update($, expanded, all => {
    if (all[id]) {
      const { [id]: _gone, ...rest } = all

      return rest
    }

    return { ...all, [id]: true as const }
  })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: COMMAND,
      description: 'Ouvre ou ferme le panneau des tâches Nestor ; avec un nom de projet, le lit',
      argumentHint: '[projet]',
    })
    await setBusy($, null)
    const known = await read($, project)
    if (known !== null) {
      void $.ui.open({ id: PANE, title: `Nestor · ${known.name}` })
    }

    return next(e)
  })

  on('command.run', { command: COMMAND }, async ($, e) => {
    const name = e.args.trim()
    if (name !== '') {
      return openProject($, name)
    }
    const pane = (await $.ui.panes()).find(one => one.id === PANE)
    if (pane?.isShown) {
      await $.ui.close({ id: PANE })

      return { text: 'Panneau Nestor fermé.' }
    }
    const known = await read($, project)
    await $.ui.open({ id: PANE, title: `Nestor · ${known?.name ?? 'tâches'}` })

    return { text: 'Panneau Nestor ouvert.' }
  })

  on('tool.call', async ($, e, next) => {
    const call = e as unknown as Loose
    const match = nestorCall(e.tool, call)
    const ran = await next(e)
    if (match === null || ran.deny !== undefined || ran.isError !== undefined) {
      return ran
    }
    const { server, name } = match
    const page = payloadOf(ran)
    if (page === null) {
      return ran
    }
    try {
      if (name === 'list_items') {
        await absorbPage($, server, call, page)
      } else if (name === 'get_item') {
        await absorbRead($, page)
      } else if (name === 'get_project') {
        await absorbProject($, page)
      } else {
        await absorbMutation($, name, call, page)
      }
    } catch (error) {
      $.ui.log(`nestor-taches : ${error instanceof Error ? error.message : String(error)}`)
    }

    return ran
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const elements = $.ui.resolve(e)
    const { Box, Button, Text } = elements
    const Markdown = 'Markdown' in elements ? elements.Markdown : undefined
    const named = await read($, project)
    const all = await read($, items)
    const known = await read($, details)
    const open = await read($, expanded)
    const total = await read($, counts)
    const src = await read($, source)
    const at = await read($, readAt)
    const isBacklogShown = await read($, showBacklog)
    const doing = await read($, busy)
    const now = Date.now()

    if (named === null) {
      return (
        <Box flexDirection="column">
          <Text weight="medium">Aucune lecture pour l'instant.</Text>
          <Text size="footnote" dimColor>
            Lance /nestor-beta:next-tasks, ou /nestor-taches suivi d'un nom de projet.
          </Text>
        </Box>
      )
    }

    const ids = new Set(all.map(one => one.id))
    const children = new Map<string, NestorEntry[]>()
    const roots: NestorEntry[] = []
    for (const one of all) {
      const parent = parentOf(one)
      if (parent !== undefined && ids.has(parent)) {
        children.set(parent, [...(children.get(parent) ?? []), one])
      } else {
        roots.push(one)
      }
    }
    const hasOpen = Object.keys(open).length > 0

    const metaLineOf = (one: NestorEntry) => (
      <Box flexDirection="row" flexWrap="wrap" columnGap={1}>
        {metaOf(one, now).flatMap((part, index) => [
          index > 0 && (
            <Text size="footnote" dimColor>
              ·
            </Text>
          ),
          <Text size="footnote" {...tint(part.color)}>
            {part.text}
          </Text>,
        ])}
      </Box>
    )

    const detailOf = (one: NestorEntry) => {
      const detail = known[one.id]
      const text = detail ? `${detail.body ?? ''}${specificationText(detail)}`.trim() : ''
      const parent = parentOf(one)
      const meta = [
        one.slug ?? one.id,
        one.type === 'task' && one.template === 'code' ? 'tâche code' : null,
        approvalText(one),
        parent !== undefined && !ids.has(parent) ? `parent non lu : ${parent}` : null,
      ]
        .filter(Boolean)
        .join(' · ')
      const isReading = doing !== null && typeof doing === 'object' && doing.detail === one.id
      const canSpec =
        one.type === 'plan'
          ? one.progress !== 'completed'
          : one.type === 'task' && one.status !== 'completed' && one.status !== 'cancelled'
      const canBuild =
        (one.type === 'task' && one.status === 'ready_to_build') ||
        (one.type === 'plan' && isApproved(one))

      return (
        <Box
          flexDirection="column"
          rowGap="xs"
          marginLeft={2}
          marginTop="xs"
          paddingX={1}
          borderStyle="round"
          borderColor="subtle"
        >
          <Text size="footnote" dimColor wrap="wrap">
            {meta}
          </Text>
          {one.tags && one.tags.length > 0 && (
            <Text size="footnote" dimColor wrap="wrap">
              {one.tags.map(tag => `#${tag.name}`).join(' ')}
            </Text>
          )}
          {!detail && one.excerpt && <Text wrap="wrap">{one.excerpt}</Text>}
          {detail &&
            (text === '' ? (
              <Text size="footnote" dimColor>
                (aucun contenu)
              </Text>
            ) : Markdown ? (
              <Markdown text={text} />
            ) : (
              <Text wrap="wrap">{text}</Text>
            ))}
          <Box flexDirection="row" flexWrap="wrap" columnGap="sm">
            {!detail && src !== null && isReading && (
              <Text size="footnote" dimColor>
                lecture…
              </Text>
            )}
            {!detail && src !== null && !isReading && (
              <Button
                key={`detail:${one.id}`}
                label="Lire le détail"
                plain
                dimColor
                onPress={() => void fetchDetail($, one.id)}
              />
            )}
            {canSpec && (
              <Button
                key={`spec:${one.id}`}
                label="Spec"
                onPress={() => void submitSkill($, 'spec', one)}
              />
            )}
            {canBuild && (
              // A primary variant could paint its own background under the orange label.
              <Button key={`build:${one.id}`} onPress={() => void submitSkill($, 'build', one)}>
                <Text color="claude" weight="semibold">
                  Build
                </Text>
              </Button>
            )}
          </Box>
        </Box>
      )
    }

    const rowOf = (one: NestorEntry): JSX.Element => {
      const isOpen = open[one.id] === true
      const mark = markOf(one)
      const kids = children.get(one.id) ?? []

      return (
        <Box flexDirection="column">
          <Box flexDirection="row" columnGap={1} alignItems="flex-start">
            <Text {...tint(mark.color)}>{mark.glyph}</Text>
            <Box flexDirection="column" flexGrow={1} flexShrink={1}>
              <Text wrap="wrap" weight={one.type === 'plan' ? 'semibold' : 'regular'}>
                {titleOf(one)}
              </Text>
              {metaLineOf(one)}
            </Box>
            <Button
              key={`row:${one.id}`}
              plain
              dimColor
              label={isOpen ? '⌄' : '›'}
              onPress={() => void toggle($, one.id)}
            />
          </Box>
          {isOpen && detailOf(one)}
          {kids.length > 0 && (
            // The glyph and its gap are two cells: a child's glyph sits under its parent's title.
            <Box flexDirection="column" rowGap="xs" paddingLeft={2} marginTop="xs">
              {kids.map(child => rowOf(child))}
            </Box>
          )}
        </Box>
      )
    }

    // A section opens wherever the server's order switches between plans and other items.
    const sections: { isPlan: boolean; rows: JSX.Element[] }[] = []
    for (const one of roots) {
      const isPlan = one.type === 'plan'
      const last = sections.at(-1)
      if (last?.isPlan === isPlan) {
        last.rows.push(rowOf(one))
      } else {
        sections.push({ isPlan, rows: [rowOf(one)] })
      }
    }

    const summary = [
      total ? `${total.active} actives` : null,
      total ? `${total.backlog} en backlog` : null,
      at !== null ? `lu à ${timeText(at)}` : null,
    ]
      .filter(Boolean)
      .join(' · ')
    const busyText =
      doing === 'refresh'
        ? 'relecture en cours…'
        : doing === 'backlog'
          ? 'lecture du backlog…'
          : doing === 'project'
            ? 'lecture du projet…'
            : null

    return (
      <Box flexDirection="column" rowGap="md">
        <Box flexDirection="column">
          <Text size="title" weight="semibold">
            {named.name}
          </Text>
          <Text size="footnote" dimColor>
            {summary}
          </Text>
        </Box>
        <Box flexDirection="row" flexWrap="wrap" columnGap="sm">
          {busyText !== null && (
            <Text size="footnote" dimColor>
              {busyText}
            </Text>
          )}
          {busyText === null && (
            <Button
              key="refresh"
              label="Rafraîchir"
              plain
              dimColor
              onPress={() => void refresh($)}
            />
          )}
          {busyText === null && (
            <Button
              key="backlog"
              label={
                isBacklogShown
                  ? 'Masquer le backlog'
                  : `Backlog${total ? ` (${total.backlog})` : ''}`
              }
              plain
              dimColor
              onPress={() => void toggleBacklog($)}
            />
          )}
          {hasOpen && (
            <Button
              key="fold"
              label="Tout replier"
              plain
              dimColor
              onPress={() => void update($, expanded, () => ({}))}
            />
          )}
          {/* The desktop pane's own header already has ⤢ and ✕. */}
          {e.surface !== 'desktop' && (
            <Button
              key="close"
              label="Fermer"
              plain
              dimColor
              onPress={() => void $.ui.close({ id: PANE })}
            />
          )}
        </Box>
        {sections.length === 0 ? (
          <Text size="footnote" dimColor>
            Aucune tâche active dans ce projet.
          </Text>
        ) : (
          <Box flexDirection="column" rowGap="md">
            {sections.map(section => (
              <Box flexDirection="column" rowGap="xs">
                <Text size="caption" weight="medium" dimColor>
                  {section.isPlan ? 'Plans' : 'Tâches'}
                </Text>
                {section.rows}
              </Box>
            ))}
          </Box>
        )}
      </Box>
    )
  })
}
