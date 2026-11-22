# Requirements map

What each step in Second Look is built to support, and where that comes from. **This is a design aid, not legal advice.** Coverage, exemptions, and what counts as an adverse outcome depend on facts and on rules not yet published. Counsel should review any use.

Sources were read on 18 November 2026.

## Colorado SB 26-189, Automated Decision-Making Technology

**Status:** signed 14 May 2026 (Chapter 131), per the [Colorado General Assembly's bill page](https://leg.colorado.gov/bills/sb26-189). The summary dates developer duties and the attorney general's rules to 1 January 2027 and gives no separate date for deployer duties. The [Playbook's 13 November 2026 source review](https://github.com/ellehelvig/hr-ai-transformation-playbook/blob/main/03-governance/review-2026-11-13.md) records the duties as applying to decisions on and after 1 January 2027. Confirm against the enrolled text.

**What was read:** the legislature's summary of the act as enacted. The enrolled text and the attorney general's rules, due by 1 January 2027, were not read. Treat every row below as a summary to confirm against the text and the rules.

| Duty in the summary | Second Look step | Enforced in code |
|---|---|---|
| Clear and conspicuous notice at the point of interaction with a covered tool | `give_notice` | Notice dated after the decision is rejected |
| Plain-language description of the tool's role within 30 days of a decision with an adverse outcome | `send_explanation`, `explanation_due` | Due date computed; a late send is logged as late; `overdue` flags it |
| Right to request the personal data the tool used | `answer_data_access` | Returns exactly the data recorded as used |
| Right to correct factually incorrect personal data the tool used | `decide_correction` | Must name a field the tool used; accept or decline needs a reason; pending corrections block the review |
| Right to request meaningful human review and reconsideration after an adverse outcome | `assign_reviewer`, `reconsider` | Reviewer cannot be the original decider or the tool; rationale required and must address corrected data |
| Keep records needed to show compliance for at least 3 years | `retain_until`, the case log | Retention date computed from the decision date |

**What the summary does not settle,** so Second Look leaves these to organization policy or counsel:

- What counts as an "adverse outcome". The summary does not define it.
- What the explanation must contain beyond the tool's role. Second Look also lists the main factors, the data used, and the person's options, because a description of the tool alone does not help someone decide whether to ask for review.
- Deadlines for answering data requests and for completing a review. `Policy` defaults both to 30 days and labels them as organization policy.
- Whether a qualifier limits the human review duty. Some secondary summaries describe one; the legislature's summary does not mention it. Check the enrolled text.
- Enforcement detail. The summary says the attorney general enforces under the Colorado Consumer Protection Act, with a 60-day notice and cure period before 1 January 2030 where a cure is possible, and no new private right of action.

## EU

| Source | Status | What it means for this flow |
|---|---|---|
| [GDPR Article 22, Regulation (EU) 2016/679](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679) | In force since 25 May 2018 | Addresses solely automated decisions with legal or similarly significant effects, subject to exceptions and safeguards. A nominal human sign-off does not settle whether it applies. Second Look's rule that a named person owns every decision is a design choice, not a compliance conclusion. |
| EU AI Act, high-risk HR systems, as amended by [Regulation (EU) 2026/1744](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32026R1744) | High-risk duties for employment uses apply from 2 December 2027 | Plan human oversight, logging, and informing workers against that date. This repository does not map the Act article by article. |

The EU dates match the Key dates table in the [HR AI Transformation Playbook](https://github.com/ellehelvig/hr-ai-transformation-playbook/blob/main/03-governance/README.md), which links each to its official text.
