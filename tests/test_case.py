import unittest
from datetime import date

from secondlook import Case, CaseError, Decision, Policy, Request
from secondlook.example import build_case


def decision(**overrides):
    values = dict(
        subject="Sam Okafor",
        decision_type="promotion review",
        outcome="not promoted this cycle",
        adverse=True,
        decided_on=date(2027, 3, 1),
        decided_by="Dana Wu",
        tool_name="Calibration Helper",
        tool_role="it summarized peer feedback into themes",
        factors=["Peer feedback themes"],
        data_used={"Projects led": "2", "Tenure in level (months)": "14"},
    )
    values.update(overrides)
    return Decision(**values)


class DecisionRules(unittest.TestCase):
    def test_tool_cannot_own_decision(self):
        with self.assertRaises(CaseError):
            decision(decided_by="tool")

    def test_factors_required(self):
        with self.assertRaises(CaseError):
            decision(factors=[])


class Timing(unittest.TestCase):
    def test_explanation_due_30_days_after_decision(self):
        self.assertEqual(Case("C1", decision()).explanation_due, date(2027, 3, 31))

    def test_retention_three_years(self):
        self.assertEqual(Case("C1", decision()).retain_until, date(2030, 3, 1))

    def test_retention_from_leap_day(self):
        self.assertEqual(Case("C1", decision(decided_on=date(2028, 2, 29))).retain_until, date(2031, 2, 28))

    def test_policy_changes_deadlines(self):
        case = Case("C1", decision(), Policy(review_days=10))
        case.receive_request(Request("review", date(2027, 3, 5)))
        self.assertEqual(case.due_date(case.requests[0]), date(2027, 3, 15))

    def test_overdue_explanation_flagged(self):
        case = Case("C1", decision())
        self.assertEqual(case.overdue(date(2027, 3, 31)), [])
        self.assertEqual(len(case.overdue(date(2027, 4, 1))), 1)

    def test_late_explanation_logged_as_late(self):
        case = Case("C1", decision())
        case.send_explanation(date(2027, 4, 2), "HR")
        self.assertIn("late", case.log[-1].what)

    def test_notice_after_decision_rejected(self):
        with self.assertRaises(CaseError):
            Case("C1", decision()).give_notice(date(2027, 3, 2), "HR")


class Explanation(unittest.TestCase):
    def test_explanation_uses_only_the_record(self):
        text = Case("C1", decision()).send_explanation(date(2027, 3, 5), "HR")
        for expected in ["Calibration Helper", "Dana Wu", "Peer feedback themes", "Projects led: 2", "case C1"]:
            self.assertIn(expected, text)
        self.assertIn("will not be the person who made the original decision", text)

    def test_no_explanation_for_favorable_decision(self):
        with self.assertRaises(CaseError):
            Case("C1", decision(adverse=False)).send_explanation(date(2027, 3, 5), "HR")


class Requests(unittest.TestCase):
    def test_data_access_returns_data_used(self):
        case = Case("C1", decision())
        case.receive_request(Request("data_access", date(2027, 3, 5)))
        self.assertEqual(case.answer_data_access(date(2027, 3, 6), "HR")["Projects led"], "2")

    def test_correction_must_name_a_used_field(self):
        case = Case("C1", decision())
        with self.assertRaises(CaseError):
            case.receive_request(Request("correction", date(2027, 3, 5), field_name="Salary", corrected_value="1"))

    def test_accepted_correction_updates_data(self):
        case = Case("C1", decision())
        case.receive_request(Request("correction", date(2027, 3, 5), field_name="Projects led", corrected_value="3"))
        case.decide_correction(date(2027, 3, 6), "HR", accept=True, reason="Project list confirms three.")
        self.assertEqual(case.decision.data_used["Projects led"], "3")

    def test_correction_decision_needs_reason(self):
        case = Case("C1", decision())
        case.receive_request(Request("correction", date(2027, 3, 5), field_name="Projects led", corrected_value="3"))
        with self.assertRaises(CaseError):
            case.decide_correction(date(2027, 3, 6), "HR", accept=False, reason=" ")


class Review(unittest.TestCase):
    def setUp(self):
        self.case = Case("C1", decision())
        self.case.receive_request(Request("review", date(2027, 3, 5)))

    def test_original_decider_cannot_review(self):
        with self.assertRaises(CaseError):
            self.case.assign_reviewer(date(2027, 3, 6), "dana wu")

    def test_tool_cannot_review(self):
        with self.assertRaises(CaseError):
            self.case.assign_reviewer(date(2027, 3, 6), "tool")

    def test_only_assigned_reviewer_records(self):
        self.case.assign_reviewer(date(2027, 3, 6), "Lee Park")
        with self.assertRaises(CaseError):
            self.case.reconsider(date(2027, 3, 9), "Someone Else", "upheld", "word " * 12)

    def test_one_line_rationale_rejected(self):
        self.case.assign_reviewer(date(2027, 3, 6), "Lee Park")
        with self.assertRaises(CaseError):
            self.case.reconsider(date(2027, 3, 9), "Lee Park", "upheld", "Agree with original.")

    def test_pending_correction_blocks_review(self):
        self.case.receive_request(Request("correction", date(2027, 3, 5), field_name="Projects led", corrected_value="3"))
        self.case.assign_reviewer(date(2027, 3, 6), "Lee Park")
        with self.assertRaises(CaseError):
            self.case.reconsider(date(2027, 3, 9), "Lee Park", "upheld", "I reviewed the full file and the feedback themes carefully today.")

    def test_rationale_must_address_corrected_field(self):
        self.case.receive_request(Request("correction", date(2027, 3, 5), field_name="Projects led", corrected_value="3"))
        self.case.decide_correction(date(2027, 3, 6), "HR", accept=True, reason="Project list confirms three.")
        self.case.assign_reviewer(date(2027, 3, 6), "Lee Park")
        with self.assertRaises(CaseError):
            self.case.reconsider(date(2027, 3, 9), "Lee Park", "upheld", "I reviewed the full file and the feedback themes carefully today.")
        self.case.reconsider(date(2027, 3, 9), "Lee Park", "upheld",
                             "Projects led is now 3, which I weighed, but tenure in level is still below the bar.")
        self.assertEqual(self.case.review_outcome, "upheld")


class Example(unittest.TestCase):
    def test_example_runs_and_changes_outcome(self):
        case, explanation = build_case()
        self.assertEqual(case.review_outcome, "changed")
        self.assertEqual(case.overdue(date(2027, 3, 1)), [])
        self.assertIn("Screening Assistant", explanation)


if __name__ == "__main__":
    unittest.main()
