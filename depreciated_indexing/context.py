"""Infrastructure for session-scoped context and logging.

This module provides tools to store and propagate session identifiers across
asynchronous tasks and to inject them into log messages for better traceability.
"""

import concurrent.futures
import contextvars
import logging
from typing import Any, Callable, ParamSpec, TypeVar

from indexing import shared_flags


_P = ParamSpec("_P")
_T = TypeVar("_T")

# Global context variable for the session ID.
INDEXING_SESSION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "indexing_session_id", default=None
)


class SessionIdLogFilter(logging.Filter):
    """A logging filter that prepends the session ID to log messages.

    If INDEXING_SESSION_ID is set in the current context, this filter prepends
    '[Session: <id>]' to the log record's message.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Modifies the log record to include the session ID if available."""
        session_id = INDEXING_SESSION_ID.get()
        if session_id:
            prefix = f"[Session: {session_id}]"
            if isinstance(record.msg, str) and not record.msg.startswith(prefix):
                record.msg = f"{prefix} {record.msg}"
        return True


class ContextPreservingThreadPoolExecutor(
    concurrent.futures.ThreadPoolExecutor
):
    """A ThreadPoolExecutor that propagates contextvars to worker threads.

    This executor captures the current contextvars at the time of submission and
    ensures they are available in the worker thread when the task executes.
    """

    def submit(
        self,
        fn: Callable[_P, _T],
        /,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> concurrent.futures.Future[_T]:
        """Submits a callable for execution, preserving the current context."""
        ctx = contextvars.copy_context()
        return super().submit(ctx.run, fn, *args, **kwargs)


def get_executor_class() -> type[concurrent.futures.ThreadPoolExecutor]:
    """Returns the executor class based on the preservation requirement."""
    if shared_flags.USE_CONTEXT_PRESERVING_EXECUTOR:
        return ContextPreservingThreadPoolExecutor
    return concurrent.futures.ThreadPoolExecutor


def reset_safely(token: contextvars.Token[Any]) -> None:
    """Resets a context variable safely, ignoring context mismatch errors.

    This is useful in asynchronous generators or other situations where the
    reset might be called from a different context than the one where the
    token was created (e.g., during generator closure).

    Args:
      token: The token returned by ContextVar.set().
    """
    try:
        token.var.reset(token)
    except (ValueError, RuntimeError):
        # This can happen if reset is called from a different context.
        # We ignore it as there is not much we can do about it during cleanup.
        logging.debug("Failed to reset context variable %s safely.", token.var.name)
