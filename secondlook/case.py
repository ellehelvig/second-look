"""The case record and the rules that move it from decision to closed review.

Every rule that matters is enforced here, in code, not left to a reviewer's
memory or a model's instructions:

- An adverse decision starts a clock for the plain-language explanation.
- A person can ask for their data, a correction, and a human review.
- The reviewer cannot be the person who made the original decision, and
  cannot be the tool.
- A reconsideration needs a written rationale, and must say how any
  correction the person asked for was handled.
- Records carry a retention date.

Deadlines that the source law does not set are organization policy, passed in
through Policy, so nobody mistakes a policy choice for a legal requirement.
Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

TOOL_ACTOR = "tool"


class CaseError(ValueError):
    """Raised when a step would break one of the case rules."""


@dataclass(frozen=True)
class Policy:
    """Timing rules. Defaults follow the sources in docs/requirements-map.md
    where those sources set a number, and are marked as policy where not."""

    explanation_days: int = 30      # Colorado SB 26-189 summary: within 30 days of the adverse decision
    retention_years: int = 3        # Colorado SB 26-189 summary: at least 3 years
    data_response_days: int = 30    # Organization policy. The summary sets no deadline
    review_days: int = 30           # Organization policy. The summary sets no deadline


@dataclass
class Decision:
    """What happened, in terms a person can check."""

    subject: str                    # Fictional person the decision is about
    decision_type: str              # For example "application screening"
    outcome: str                    # For example "not advanced to interview"
    adverse: bool
    decided_on: date
    decided_by: str                 # The accountable person, never the tool
    tool_name: str
    tool_role: str                  # What the tool did, in plain words
    factors: list[str]              # Main factors the tool's output reflected
    data_used: dict[str, str]       # Data field to value, as the tool saw it
    other_inputs: list[str] = field(default_factory=list)  # What the person also weighed

    def __post_init__(self) -> None:
        if self.decided_by.strip().lower() in {"", TOOL_ACTOR}:
            raise CaseError("A person must own the decision. The tool cannot be the decision owner.")
        if not self.factors:
            raise CaseError("Record the main factors, or the explanation cannot say anything useful.")


@dataclass
class Request:
    kind: str                       # "data_access", "correction", or "review"
    received_on: date
    detail: str = ""
    field_name: str | None = None   # For a correction: which data field
    corrected_value: str | None = None
    resolved_on: date | None = None
    resolution: str = ""


@dataclass
class Event:
    on: date
    actor: str
    what: str


@dataclass
class Case:
    case_id: str
    decision: Decision
    policy: Policy = field(default_factory=Policy)
    notice_given_on: date | None = None
    explanation_sent_on: date | None = None
    requests: list[Request] = field(default_factory=list)
    reviewer: str | None = None
    review_outcome: str | None = None     # "upheld" or "changed"
    review_rationale: str = ""
    log: list[Event] = field(default_factory=list)

    # ----- steps -----------------------------------------------------------

    def give_notice(self, on: date, by: str) -> None:
        """Notice that a covered tool is in use, at the point of interaction."""
        if on > self.decision.decided_on:
            raise CaseError("Notice must come at or before the point of interaction, not after the decision.")
        self.notice_given_on = on
        self._record(on, by, "Notice given that an automated tool is used in this decision.")

    def send_explanation(self, on: date, by: str) -> str:
        if not self.decision.adverse:
            raise CaseError("Explanations in this flow are for adverse decisions.")
        from .explain import explanation_text

        text = explanation_text(self)
        self.explanation_sent_on = on
        late = " (late)" if on > self.explanation_due else ""
        self._record(on, by, f"Plain-language explanation sent{late}.")
        return text

    def receive_request(self, request: Request) -> None:
        if request.kind not in {"data_access", "correction", "review"}:
            raise CaseError(f"Unknown request type: {request.kind}")
        if request.kind == "correction":
            if request.field_name not in self.decision.data_used:
                raise CaseError("A correction must name a data field the tool used.")
            if not request.corrected_value:
                raise CaseError("A correction must say what the value should be.")
        if request.kind == "review" and not self.decision.adverse:
            raise CaseError("Human review in this flow is for adverse decisions.")
        self.requests.append(request)
        self._record(request.received_on, self.decision.subject, f"Requested {request.kind.replace('_', ' ')}.")

    def answer_data_access(self, on: date, by: str) -> dict[str, str]:
        request = self._open("data_access")
        request.resolved_on, request.resolution = on, "Data the tool used was sent."
        self._record(on, by, "Sent the data the tool used.")
        return dict(self.decision.data_used)

    def decide_correction(self, on: date, by: str, accept: bool, reason: str) -> None:
        if not reason.strip():
            raise CaseError("Say why a correction was accepted or declined.")
        request = self._open("correction")
        if accept:
            self.decision.data_used[request.field_name] = request.corrected_value
        request.resolved_on = on
        request.resolution = ("Accepted: " if accept else "Declined: ") + reason
        self._record(on, by, f"Correction to '{request.field_name}' {'accepted' if accept else 'declined'}.")

    def assign_reviewer(self, on: date, reviewer: str) -> None:
        self._open("review")
        name = reviewer.strip()
        if name.lower() in {"", TOOL_ACTOR}:
            raise CaseError("A person must do the review. The tool cannot review its own output.")
        if name.lower() == self.decision.decided_by.strip().lower():
            raise CaseError("The reviewer cannot be the person who made the original decision.")
        self.reviewer = name
        self._record(on, "HR operations", f"Review assigned to {name}.")

    def reconsider(self, on: date, reviewer: str, outcome: str, rationale: str) -> None:
        request = self._open("review")
        if reviewer != self.reviewer:
            raise CaseError("Only the assigned reviewer can record the review.")
        if outcome not in {"upheld", "changed"}:
            raise CaseError("Outcome must be 'upheld' or 'changed'.")
        if len(rationale.split()) < 10:
            raise CaseError("Write a rationale someone else could follow, not a one-line sign-off.")
        if any(r.kind == "correction" and r.resolved_on is None for r in self.requests):
            raise CaseError("Decide every pending correction before the review, so the review sees the right data.")
        corrected = [r.field_name for r in self.requests if r.kind == "correction" and r.resolution.startswith("Accepted")]
        if corrected and not any(f.lower() in rationale.lower() for f in corrected):
            raise CaseError(f"The rationale must say how the corrected data was weighed: {', '.join(corrected)}.")
        self.review_outcome, self.review_rationale = outcome, rationale
        request.resolved_on, request.resolution = on, f"Review {outcome}."
        self._record(on, reviewer, f"Human review completed: decision {outcome}.")

    # ----- dates and status ------------------------------------------------

    @property
    def explanation_due(self) -> date:
        return self.decision.decided_on + timedelta(days=self.policy.explanation_days)

    @property
    def retain_until(self) -> date:
        d = self.decision.decided_on
        try:
            return d.replace(year=d.year + self.policy.retention_years)
        except ValueError:  # 29 February
            return d.replace(year=d.year + self.policy.retention_years, day=28)

    def due_date(self, request: Request) -> date:
        days = self.policy.review_days if request.kind == "review" else self.policy.data_response_days
        return request.received_on + timedelta(days=days)

    def overdue(self, today: date) -> list[str]:
        items = []
        if self.decision.adverse and self.explanation_sent_on is None and today > self.explanation_due:
            items.append(f"Explanation was due {self.explanation_due.isoformat()}.")
        for r in self.requests:
            if r.resolved_on is None and today > self.due_date(r):
                items.append(f"{r.kind.replace('_', ' ').capitalize()} request was due {self.due_date(r).isoformat()}.")
        return items

    # ----- helpers -----------------------------------------------------------

    def _open(self, kind: str) -> Request:
        for r in self.requests:
            if r.kind == kind and r.resolved_on is None:
                return r
        raise CaseError(f"No open {kind.replace('_', ' ')} request.")

    def _record(self, on: date, actor: str, what: str) -> None:
        self.log.append(Event(on, actor, what))
