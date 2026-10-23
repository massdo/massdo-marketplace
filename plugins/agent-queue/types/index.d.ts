/** A row of the desktop app's `list_sessions` (and `get_session`), the fields this mod reads. */
export type Session = {
  sessionId: string
  title?: string
  cwd: string
  isArchived: boolean
  isRunning: boolean
  lastActivityAt: string
  link?: string
  /** The session that started it: a btw, a fork, a session Claude started (`list_sessions`). */
  startedBy?: string
  /** The same, as `get_session` names it. */
  parentSessionId?: string
}

/**
 * The desktop app's own record of a session, one JSON file per session under
 * ~/Library/Application Support/Claude/claude-code-sessions/<account>/<org>/: the fields this mod reads.
 */
export type AppSession = {
  /** The id `$.session.id()` answers in that session. */
  cliSessionId?: string
  /** The project folder, where `cwd` may be a worktree of it. */
  originCwd?: string
  /** When the person last brought it on screen. */
  lastFocusedAt?: number
  /** The app's verdict on the last turn: `blocked` and `need_input` wait on the person. */
  postTurnSummary?: { status_category?: string; needs_action?: string }
  /** The turn's wrap-up, which overrides that verdict: `needsUser` is the question it leaves. */
  turnWrapUp?: { needsUser?: string }
  /** The session it was forked from (a btw, a fork). */
  spawnedFrom?: { sessionId?: string }
}

/** What `get_window_layout` says is on screen, the fields this mod reads. */
export type Layout = {
  main_window?: { tab?: string; panes?: { kind?: string; session_id?: string; focused?: boolean }[] }
  popout_windows?: { sessions?: (string | { session_id?: string })[] }
}

/** Claude Code's four states: a question for the person, finished and unseen, working, idle. */
export type Status = 'question' | 'done' | 'busy' | 'idle'

/** One session as the pane draws it: questions, then finished, working, idle; a session's children under it. */
export type Row = {
  id: string
  project: string
  title: string
  status: Status
  at: number
  /** When the person last looked at it: a finished one seen since `at` is idle. */
  seenAt: number
  age: string
  link: string
  isShown: boolean
  /** The session the main window has the focus on: where the person is. */
  isFocused: boolean
  /** The session it was started from, when it is a btw, a fork or a session Claude started. */
  parent?: string
  /** The question it waits on, when the app has its text. */
  detail?: string
}

/**
 * Why the leader could not read the app: a permission to give, a refusal, or an error.
 * `retryAt`, a refusal's only: when the leader reads again by itself (absent, at once).
 */
export type Problem = { kind: 'ask' | 'refused' | 'error'; text: string; retryAt?: number }

/** What the leader shares with every session in ~/.claude/agent-queue/state.json. */
export type Shared = { rows: Row[]; problem: Problem | null }

/** One waiting session in ~/.claude/agent-queue/queue.json, in the order the shortcut visits them. */
export type Waiting = { id: string; link: string; seenAt: number }

declare module 'claude-code' {
  interface PluginState {
    'agent-queue': { rows: Row[]; problem: Problem | null }
  }
}
