# Feature Specification: Purdue Policy Chatbot

**Feature Branch**: `001-purdue-policy-chatbot`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Build a chatbot for Purdue Northwest to help
undergraduate students and graduate students find common university questions
on things such as adding or dropping classes, academic standing, grade appeals,
financial aid deadlines, registration, and who students should contact.
Additionally, the chatbot cannot give the students incorrect or outdated
information and if the chatbot is not confident in its answer it should redirect
the student to contact someone relevant. The chatbot is going to be trained on
Purdue Northwest policy documents and webpages. Meaning that the chatbot must be
able to parse html, doc, and pdf documents. The parser must be able to handle
many different kinds of formatting such as html tables, bullet points, and side
bars."

## Clarifications

### Session 2026-09-16

- Q: For the first release, should the system include a source-management workflow for university staff as well as the student-facing chatbot? → A: Student-facing chatbot only; approved sources will be prepared outside the product.
- Q: When a student’s question depends on undergraduate or graduate status, term, or campus, should the chatbot ask for the missing detail before giving an answer? → A: Ask only when needed to distinguish between different valid rules or deadlines.
- Q: For the first release, should the chatbot be a standalone web app that students access directly, or should it be embedded into an existing Purdue Northwest site or portal? → A: Standalone web app; students access it directly.
- Q: Should the first release be public to any student without Purdue sign-in, or restricted to authenticated Purdue Northwest users only? → A: Public to any student without Purdue sign-in.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find an Answer to a Common University Question (Priority: P1)

As a Purdue Northwest undergraduate or graduate student, I want to ask a
question in ordinary language about university policies, deadlines, procedures,
or contacts so that I can find relevant official information without searching
many university pages myself.

**Why this priority**: Answering common student questions is the primary user
value and the minimum viable experience.

**Independent Test**: Ask representative questions about registration, adding or
dropping classes, academic standing, grade appeals, financial aid deadlines,
and student contacts; verify that each response addresses the question using
approved Purdue Northwest information or safely declines to answer.

**Acceptance Scenarios**:

1. **Given** approved source information covers a student's question, **When**
   the student asks the question, **Then** the chatbot provides a concise answer
   grounded in that information and identifies the relevant source.
2. **Given** the question has different rules for undergraduate and graduate
   students, **When** the student identifies their student type or provides
   enough context, **Then** the chatbot applies the applicable distinction and
   does not combine conflicting rules.
3. **Given** the question is ambiguous but can be resolved with a focused
   follow-up, **When** the chatbot asks for the missing context, **Then** it
   requests only the information needed to distinguish the applicable answer.

---

### User Story 2 - Receive a Safe Referral When Information Is Unreliable (Priority: P1)

As a student, I want the chatbot to acknowledge when it cannot reliably answer
so that I do not act on incorrect, outdated, or unofficial university policy.

**Why this priority**: Preventing harmful misinformation is a non-negotiable
requirement for policy and deadline questions.

**Independent Test**: Ask questions with no supporting source, conflicting
sources, expired deadlines, or insufficient student context; verify that the
chatbot does not invent an answer and provides a relevant university office or
official contact path when one is available.

**Acceptance Scenarios**:

1. **Given** no approved source supports the question, **When** the student asks
   it, **Then** the chatbot clearly states that it cannot provide a reliable
   answer and directs the student to an appropriate university office or
   official source.
2. **Given** approved sources conflict or their current validity cannot be
   established, **When** the student asks about the affected policy or deadline,
   **Then** the chatbot identifies the uncertainty, avoids selecting an
   unsupported answer, and provides an escalation path.
3. **Given** a student asks for individualized advice beyond the available
   policy information, **When** the chatbot responds, **Then** it distinguishes
   general information from individualized determination and directs the student
   to the responsible office.

---

### User Story 3 - Maintain a Searchable Source Set (Priority: P1)

As a university content administrator, I want Purdue Northwest policy documents
and webpages to be incorporated with their structure and source metadata intact
so that student answers remain traceable to current approved information.

**Why this priority**: Reliable answers depend on preserving the meaning and
context of the source material used to answer questions.

**Independent Test**: Provide representative HTML, DOC/DOCX, and PDF sources
containing headings, paragraphs, tables, bullet lists, and sidebars; verify that
the resulting searchable content preserves the information and its source
location well enough to answer questions accurately.

**Acceptance Scenarios**:

1. **Given** an HTML page with headings, tables, bullet points, and sidebar
   content, **When** it is added to the approved source set, **Then** those
   elements are available as distinct, correctly ordered information rather
   than being silently discarded or merged misleadingly.
2. **Given** a DOC/DOCX or PDF policy document with headings, tables, lists, and
   sidebar or callout content, **When** it is added to the approved source set,
   **Then** the meaningful text and relationships are retained for search and
   citation.
3. **Given** a source is updated or removed, **When** the source set is
   refreshed, **Then** the chatbot no longer presents superseded or removed
   content as current without clearly identifying its status.
4. **Given** a source cannot be parsed reliably, **When** it is processed, **Then**
   the source is flagged for review and its unverified content is not used as
   authoritative answer material.

---

### User Story 4 - Identify Relevant Contacts (Priority: P2)

As a student who needs help completing a university process, I want the chatbot
to identify the appropriate office, department, or contact information so that I
know where to get an authoritative decision or case-specific assistance.

**Why this priority**: Referral is the required safe fallback and a useful
outcome even when the chatbot cannot resolve the entire question.

**Independent Test**: Ask who to contact for registration, financial aid,
academic standing, grade appeals, and adding or dropping classes; verify that
the response names the responsible contact based on approved source material.

**Acceptance Scenarios**:

1. **Given** an approved source identifies a responsible office or contact,
   **When** the student asks who to contact, **Then** the chatbot provides the
   contact information and explains the relevant reason for the referral.
2. **Given** no current contact can be verified, **When** the student asks who
   to contact, **Then** the chatbot says it cannot verify the contact and points
   the student to an official Purdue Northwest directory or website.

### Edge Cases

- A deadline may be term-specific, campus-specific, student-type-specific, or
  affected by a late-change exception; the chatbot must not generalize across
  these distinctions without support.
- A source may contain conflicting dates, duplicate content, broken links, or
  an explicit expiration or supersession notice.
- A document may contain scanned or image-only pages, malformed markup, unusual
  table layouts, nested lists, or sidebar text that is visually separated from
  the main content.
- A student's question may be incomplete, use an acronym, contain a typo, or
  combine multiple unrelated requests.
- A student may ask for a decision about their individual eligibility or case
  when the source material only describes general policy.
- A source may be inaccessible, unavailable during refresh, or updated after a
  previous answer was given.
- The chatbot may receive a question outside Purdue Northwest policies or
  unrelated to university processes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chatbot MUST accept natural-language questions from Purdue
  Northwest undergraduate and graduate students.
- **FR-002**: The chatbot MUST support questions about adding or dropping
  classes, academic standing, grade appeals, financial aid deadlines,
  registration, and relevant student contacts.
- **FR-003**: The chatbot MUST answer policy, rule, deadline, and procedure
  questions only from approved Purdue Northwest information.
- **FR-004**: Every answer presenting university-specific information MUST
  identify the supporting official source or provide an accessible path to it.
- **FR-005**: The chatbot MUST preserve and apply material distinctions such as
  undergraduate versus graduate status, academic term, campus, program, and
  applicable deadline when those distinctions are present in the source.
- **FR-006**: The chatbot MUST ask a targeted follow-up question when required
  context is missing and a follow-up can reasonably resolve the ambiguity, but
  it SHOULD avoid asking for unnecessary detail when the answer can be safely
  limited to the applicable rule or a referral.
- **FR-007**: The chatbot MUST NOT present unsupported, invented, or unverifiable
  information as official Purdue Northwest policy.
- **FR-008**: When reliable information is insufficient, conflicting, outdated,
  or unavailable, the chatbot MUST clearly state that it cannot provide a
  reliable answer.
- **FR-009**: When it cannot reliably answer, the chatbot MUST direct the
  student to the most relevant verified university office, contact, or official
  source when one is available.
- **FR-010**: The chatbot MUST distinguish general policy information from
  individualized decisions and MUST refer students to the responsible office
  for case-specific determinations.
- **FR-011**: The source process MUST accept HTML, DOC/DOCX, and PDF policy
  documents and webpages.
- **FR-012**: The source process MUST preserve meaningful content from headings,
  paragraphs, HTML tables, document tables, bullet lists, numbered lists,
  sidebars, and callouts.
- **FR-013**: The source process MUST retain source identity, location, and
  freshness metadata sufficient to trace an answer to the originating document
  or webpage.
- **FR-014**: The source process MUST identify parsing failures, inaccessible
  sources, and content that cannot be verified, and MUST prevent such content
  from being treated as authoritative until reviewed.
- **FR-015**: The source process MUST support replacing, removing, or marking
  superseded sources so that outdated information is not presented as current.
- **FR-016**: The chatbot MUST provide understandable responses for supported
  questions and explain what additional context is needed when it cannot answer
  directly.
- **FR-017**: The chatbot MUST handle questions that are outside the approved
  Purdue Northwest source set by using the safe-failure and referral behavior.
- **FR-018**: The system MUST record enough answer and source status information
  for authorized reviewers to investigate whether a response was grounded,
  current, and appropriately escalated.
- **FR-019**: For the first release, the product scope is limited to a
  student-facing chatbot; approved Purdue Northwest source content is prepared
  outside the product and loaded into the chatbot's knowledge base.
- **FR-020**: For the first release, the chatbot MUST be delivered as a
  standalone web application that students can access directly without a
  separate portal or embedded widget integration.
- **FR-021**: For the first release, access MUST be open to students without
  Purdue Northwest sign-in; the chatbot is a public-facing informational tool.

### Key Entities

- **Approved Source**: An authorized Purdue Northwest webpage or policy
  document, including its title, source location, owner or issuing office,
  effective or publication date, review status, and supersession status.
- **Source Content Segment**: A traceable portion of an approved source,
  preserving its meaningful text, structural context, and location.
- **Student Question**: A student's natural-language request, including
  supplied context such as student type, term, campus, or program.
- **Grounded Answer**: A response supported by one or more current approved
  source segments and accompanied by source access information.
- **Safe Referral**: A clear statement of insufficient reliability plus the
  verified office, contact, or official source the student should use next.
- **Parsing Review Record**: A record of a source processing issue, its impact,
  review status, and whether the affected content is allowed for answering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In evaluation sets composed of supported common questions, at
  least 95% of responses identify the correct applicable policy or procedure and
  cite the supporting approved source.
- **SC-002**: In evaluation sets containing unsupported, conflicting, stale, or
  insufficiently contextualized questions, at least 99% of responses avoid
  presenting an unsupported university policy and provide a clear safe-failure
  or referral response.
- **SC-003**: At least 95% of representative HTML, DOC/DOCX, and PDF sources
  containing headings, tables, lists, and sidebars retain the relevant
  information and structural context needed for a reviewer to locate it.
- **SC-004**: At least 90% of students in usability evaluation can find either
  a usable answer or an appropriate university contact within 3 minutes for
  each supported question category.
- **SC-005**: At least 90% of usability participants correctly understand
  whether a response is an official-information answer, a request for more
  context, or a referral to a university office.
- **SC-006**: Authorized reviewers can trace 100% of sampled policy answers to
  the source document or webpage and the specific supporting content.
- **SC-007**: Superseded or removed sources produce no current-policy answers in
  post-refresh evaluation unless the response explicitly identifies them as
  historical or unavailable.
- **SC-008**: For common supported questions, 90% of users receive an initial
  response or a targeted clarification request within 5 seconds under normal
  service conditions.

## Assumptions

- Purdue Northwest offices or designated administrators will identify which
  webpages and documents are approved sources and will provide access to them.
- The first release is limited to a student-facing chatbot; source approval,
  refresh, and removal workflows are handled outside the product and the
  resulting approved source set is loaded into the chatbot's knowledge base.
- The first release is a standalone web application accessed directly by
  students; it is not an embedded portal widget or a backend-only service.
- The first release is publicly accessible without Purdue sign-in; it is not a
  gated campus-only service.
- Source ownership, publication or effective dates, and supersession status can
  be obtained or reviewed when the source is added or refreshed.
- The first release supports English-language Purdue Northwest content.
- Students are not required to sign in to ask general policy questions; the
  chatbot will not make authenticated eligibility decisions.
- The chatbot provides general information and referrals, not legal, financial,
  academic, or enrollment decisions for an individual student's case.
- Contact information is considered authoritative only when it is current in an
  approved Purdue Northwest source.
- Image-only or otherwise inaccessible source content may require human review
  before it can be used as authoritative information.
- Mobile and desktop access are both expected, but exact presentation details
  are outside this specification.

## Out of Scope

- Making enrollment, grade, financial aid, or academic standing decisions.
- Submitting registration changes, appeals, financial aid applications, or other
  transactions on a student's behalf.
- Answering questions using unofficial sources, user-provided policy claims, or
  unsupported general knowledge as if they were Purdue Northwest policy.
- Replacing university staff who provide individualized advising or case
  resolution.
