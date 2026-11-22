"""Builds the plain-language explanation from the case record.

Templates only, no model. Every sentence comes from a field someone recorded,
so the explanation can never say more than the record supports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .case import Case


def _list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def explanation_text(case: "Case") -> str:
    d = case.decision
    weighed = (
        f"\nThe person who decided also considered:\n\n{_list(d.other_inputs)}\n" if d.other_inputs else ""
    )
    data = _list([f"{k}: {v}" for k, v in d.data_used.items()])
    return f"""Subject: How a tool was used in your {d.decision_type}

Dear {d.subject},

On {d.decided_on.day} {d.decided_on:%B %Y}, the outcome of your {d.decision_type} was: {d.outcome}.

A tool called {d.tool_name} was part of this decision. Its role: {d.tool_role}. The tool did not make the decision. It was made by {d.decided_by}, who is accountable for it.

The main factors reflected in the tool's output were:

{_list(d.factors)}
{weighed}
The tool used this information about you:

{data}

What you can do:

- Ask for a copy of the personal data the tool used.
- Ask us to correct any of that data that is factually wrong.
- Ask for a person to review and reconsider the decision. The reviewer will not be the person who made the original decision.

To make any of these requests, reply to this message or use the contact in your original notice. Reference: case {case.case_id}.
"""
