export type NestorProject = { id: string; name: string }

export type NestorTag = { id: string; name: string }

export type NestorDate = { instant: string } | { date: string; isAllDay: true }

export type NestorApproval = { workRevision: number; approvedAt: string }

export type NestorTaskStatus =
  | 'todo'
  | 'ready_to_build'
  | 'building'
  | 'in_progress'
  | 'need_review'
  | 'completed'
  | 'cancelled'

export type NestorPriority = 'low' | 'normal' | 'high' | 'urgent'

export type NestorProgress = 'not_started' | 'in_progress' | 'blocked' | 'completed'

export type NestorTask = {
  id: string
  type: 'task'
  title: string
  slug?: string
  excerpt?: string
  status: NestorTaskStatus
  priority: NestorPriority
  scheduledAt?: NestorDate
  dueAt?: NestorDate
  backlog: boolean
  parentTaskId?: string
  planId?: string
  template?: 'code'
  workRevision?: number
  approval?: NestorApproval
  project?: NestorProject
  tags?: NestorTag[]
}

export type NestorPlan = {
  id: string
  type: 'plan'
  title: string
  slug?: string
  excerpt?: string
  parentPlanId?: string
  workRevision?: number
  approval?: NestorApproval
  progress?: NestorProgress
  project?: NestorProject
  tags?: NestorTag[]
}

export type NestorNote = {
  id: string
  type: 'note'
  title?: string
  slug?: string
  excerpt?: string
  project?: NestorProject
  tags?: NestorTag[]
}

export type NestorItem = NestorTask | NestorPlan | NestorNote

/** An item of the pane: listed by a read, or read as an ancestor outside the view. */
export type NestorEntry = NestorItem & { isContext?: true }

export type NestorStep = { action?: string; verification?: string }

export type NestorSpecification = {
  context?: string
  steps?: NestorStep[]
  doneWhen?: string[]
  repository?: string
}

export type NestorDetail = {
  body?: string
  specification?: NestorSpecification
  readAt: number
}

export type NestorCounts = { active: number; backlog: number }

/** The Nestor server and the plugin hash of the last captured call: what the pane's own calls need. */
export type NestorSource = { server: string; versionHash: string }

/** What the pane is reading on its own right now, so its buttons wait. */
export type NestorBusy = 'refresh' | 'backlog' | 'project' | { detail: string }

declare module 'claude-code' {
  interface PluginState {
    'nestor-beta': {
      project: NestorProject | null
      items: NestorEntry[]
      details: Record<string, NestorDetail>
      expanded: Record<string, true>
      counts: NestorCounts | null
      source: NestorSource | null
      readAt: number | null
      showBacklog: boolean
      busy: NestorBusy | null
    }
  }
}
