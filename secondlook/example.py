"""A fictional end-to-end case. All people, companies, and tools are invented."""

from __future__ import annotations

from datetime import date

from .case import Case, Decision, Request


def build_case() -> tuple[Case, str]:
    decision = Decision(
        subject="Jordan Rivera",
        decision_type="application for Operations Analyst at Larkspur Freight",
        outcome="not advanced to interview",
        adverse=True,
        decided_on=date(2027, 2, 3),
        decided_by="Priya Shah, Recruiting Manager",
        tool_name="Screening Assistant",
        tool_role="it compared the application to the job's listed requirements and sorted applications into three groups for the recruiter to read first, second, or last",
        factors=[
            "Years of experience with SQL reported in the application",
            "Whether a logistics or supply chain role appeared in work history",
        ],
        data_used={
            "SQL experience (years)": "1",
            "Logistics or supply chain role": "No",
            "Location": "Denver, CO",
        },
        other_inputs=["The written application, read in full"],
    )
    case = Case("LF-2027-0142", decision)
    case.give_notice(date(2027, 1, 20), "Larkspur careers site")
    explanation = case.send_explanation(date(2027, 2, 10), "HR operations")

    case.receive_request(Request("correction", date(2027, 2, 14), "I have 4 years of SQL from my analyst role.",
                                 field_name="SQL experience (years)", corrected_value="4"))
    case.receive_request(Request("review", date(2027, 2, 14), "Please look again with the right SQL figure."))
    case.decide_correction(date(2027, 2, 18), "HR operations", accept=True,
                           reason="The resume shows SQL work from 2022 to 2026; the form field was misread.")
    case.assign_reviewer(date(2027, 2, 18), "Marcus Lee, Talent Acquisition Lead")
    case.reconsider(
        date(2027, 2, 25),
        "Marcus Lee, Talent Acquisition Lead",
        "changed",
        "With SQL experience (years) corrected to 4, the application meets the requirement that drove the "
        "low grouping. I read the full application and work history. Advancing to a recruiter screen.",
    )
    return case, explanation


def run() -> str:
    case, explanation = build_case()
    lines = [f"Case {case.case_id}", "", "Timeline:"]
    lines += [f"  {e.on.isoformat()}  {e.actor}: {e.what}" for e in case.log]
    lines += [
        "",
        f"Explanation due: {case.explanation_due.isoformat()}",
        f"Keep records until: {case.retain_until.isoformat()}",
        f"Overdue on 2027-03-01: {case.overdue(date(2027, 3, 1)) or 'nothing'}",
        "",
        "Explanation sent:",
        "",
        explanation,
    ]
    return "\n".join(lines)
