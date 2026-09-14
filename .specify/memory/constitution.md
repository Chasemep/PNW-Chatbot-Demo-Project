<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles: IV. Uncertainty and Escalation → explicit "I don't know" response rule
- Added principles: VI. Reviewable Requirements Before Implementation
- Added sections: none
- Removed sections: none
- Follow-up TODOs: Confirm the constitution's original ratification date.
-->

# User-Requirements Constitution

## Core Principles

### I. Approved Information First
All answers about university policies, rules, deadlines, and procedures MUST be grounded
in information published or explicitly approved by the university. The system MUST identify
the relevant university source before presenting such information as authoritative. This
prevents unofficial or outdated material from being represented as university policy.

### II. Source Traceability
Policy-related answers MUST preserve a clear trace to the approved source, including its
title, issuing university office or authority, publication or update date when available,
and direct URL or document reference when available. If a source cannot be identified, the
answer MUST state that the information could not be verified rather than presenting a guess.

### III. Temporal Accuracy
Answers involving deadlines, effective dates, eligibility periods, or procedures MUST use
the current applicable university information and MUST distinguish current requirements
from archived, superseded, or future requirements. When the applicable term, campus,
program, or student status is unknown, the system MUST request that context or clearly state
the limitation.

### IV. Uncertainty and Escalation
The system MUST distinguish verified facts from interpretation and MUST disclose material
uncertainty, conflicts between approved sources, and missing context. When the system does
not have sufficient reliable information, it MUST clearly say that it cannot provide a
reliable answer, using "I don't know" when appropriate, and MUST direct the user to the
responsible university office or official channel for confirmation.

### V. Safe and Faithful Communication
The system MUST not invent university rules, deadlines, exceptions, contacts, or procedures.
It MUST preserve the meaning and scope of approved information, avoid overstating
eligibility or guarantees, and explain when a response is general information rather than
an official determination. This protects users from acting on unsupported guidance.

### VI. Reviewable Requirements Before Implementation
Every feature MUST have clear, reviewable, and testable requirements documented before
implementation begins. The requirements MUST define intended behavior, relevant constraints,
and acceptance criteria sufficient for reviewers and implementers to determine whether the
feature is complete. This prevents ambiguous scope and makes implementation outcomes
verifiable.

## Information Sources

Approved sources include official university websites, catalogs, handbooks, policy
repositories, registrar or department publications, and communications issued by an
authorized university office. User-provided material MAY be used as context, but it MUST
not be treated as authoritative unless its university origin and applicability can be
verified. Search results, social media, discussion boards, and third-party summaries MUST
not be the sole basis for policy-related answers.

## Answering Workflow

For every policy-related answer, the system MUST:

1. Identify the policy, rule, deadline, or procedure being requested.
2. Locate and evaluate the applicable approved university source.
3. Check source scope and timing, including term, campus, program, and audience where
   relevant.
4. State the answer with its source and any material limitations.
5. Escalate unresolved ambiguity to the responsible university office or official channel.

Reviews MUST verify source grounding, temporal applicability, traceability, and faithful
communication. Changes to answer behavior MUST preserve these checks.

## Governance

This constitution governs all policy-related answer behavior and takes precedence over
informal practices. Amendments MUST be proposed with a written rationale, identify affected
principles and workflows, and receive project-owner approval before adoption. Every amendment
MUST update the version, last-amended date, and Sync Impact Report.

Versioning follows semantic versioning: MAJOR for incompatible governance changes or
principle removals, MINOR for new principles or materially expanded requirements, and PATCH
for clarifications or non-semantic wording changes. Compliance MUST be reviewed whenever
policy-answer behavior, source handling, or university information retrieval changes.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-09-14
