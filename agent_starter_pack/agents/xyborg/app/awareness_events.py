"""Awareness event catalog for {{cookiecutter.agent_directory}}.

Single source of truth for every awareness event this agent fires. Each
event is declared once here as an ``AwarenessEventSpec`` constant; every
emit/check site imports the constant by name. A typo at any callsite
becomes a NameError at import time, not a feature that silently fails
at runtime.

See ``common/context/awareness.py`` for the underlying primitives:
  - ``AwarenessEventSpec`` — the dataclass declared below.
  - ``EventStatus`` — three-value enum (PENDING / COMPLETE / FAILED).
  - ``record_event(spec, state, **fields)`` — write a payload to state.
  - ``inform_agent(spec, state)`` — queue the event for prompt injection
    on the next model turn. Pure announcement; does not touch state.
  - ``register_awareness(spec)`` — declare the spec at import time.
  - ``validate_awareness_registry([spec, ...])`` — startup check that
    every required spec is registered (catches "forgot to import"
    silent-failure bugs).

USAGE PATTERN (uncomment + adapt):

  1. Define the spec here (one constant per event).
  2. In bootstrap.py, import each spec and call register_awareness(spec).
     Then call validate_awareness_registry([spec, ...]) inside bootstrap().
  3. At the emit site (a tool, a sub-agent callback, etc.):

       record_event(MY_EVENT, state, foo="x", bar="y")

     This writes the payload to state[spec.state_key] WITHOUT queueing
     the announcement. The next model turn's check_awareness picks it up
     and announces — that's the right pattern for async-task
     completions where the work is done by background machinery.

  4. For sync-fire sites (events that need to surface in the SAME turn
     they fired in — e.g. "user just reconnected", "session recovered
     from disk"), call BOTH:

       record_event(MY_EVENT, state, foo="x", bar="y")
       inform_agent(MY_EVENT, state)

     The split exists because state-as-truth and prompt-as-announcement
     are conceptually distinct — sometimes you want to record an event
     for diagnostics without injecting into the next turn.

  5. For failure paths:

       record_event(MY_EVENT, state,
                    status=EventStatus.FAILED, error=str(exc))

     The renderer surfaces this as "<event_name> failed: <error>" in
     the prompt — no success header/footer. The model composes the
     user-facing failure message itself; you don't have to write
     per-event failure text.

  6. In before_model_callback, register the spec for awareness checking:

       awareness_checks=[partial(check_awareness, spec=MY_EVENT)]
"""

# Uncomment when you add your first event:
# from common.context.awareness import AwarenessEventSpec, AwarenessLevel


# ─── Example event spec (commented out — copy/adapt for your agent) ─────
#
# Awareness levels:
#   ANNOUNCED — agent proactively surfaces (use for state-changing events)
#   INFORMED  — agent weaves in when relevant
#   SILENT    — agent has the info but only mentions if asked
#
# fields: tuple of declared field names. ALL are required when emitting
#   with status=COMPLETE (the default). Validator raises ValueError if
#   you forget one. Extra (undeclared) fields warn but don't crash.
#
# header: opening line shown above the rendered fields.
# footer: closing directive — what should the model do about this event?
#   Optional. Used for events that imply the agent should take action
#   (announce something, ask a question, gate a tool call).
#
# state_key: the dict key where the payload is stored.
#   Convention: same as `name`. Different only if the event reports on
#   something that already lives under a different key in state.
#
# EXAMPLE_EVENT = AwarenessEventSpec(
#     name="example_event",
#     level=AwarenessLevel.ANNOUNCED,
#     state_key="example_event",
#     fields=("user_id", "result_summary"),
#     header="Example task completed:",
#     footer=(
#         "Surface the result_summary to the user and ask whether they "
#         "want to take any follow-up action."
#     ),
# )


# ─── Convenience: collect specs for validate_awareness_registry() ──────
# Listing every spec here makes a "did I import this module?" startup
# check in bootstrap() trivial. Add specs to this tuple as you declare them.
ALL_SPECS: tuple = (
    # EXAMPLE_EVENT,
)
