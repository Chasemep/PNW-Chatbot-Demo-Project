# Feature Specification: Authoritative University Information Chatbot

**Feature Branch**: `001-authoritative-university-chatbot`

**Created**: 2026-09-14

**Status**: Draft

**Input**: User description: Build a conversational Purdue University Northwest chatbot that answers questions about programs, admissions, campus life, policies, deadlines, registration, and related university topics using accurate, current, approved university information.

## Clarifications

### Session 2026-09-17

- Q: Should the initial chatbot be available to anyone without signing in, or require Purdue Northwest authentication? → A: Public access without signing in.
- Q: How should the initial release verify that time-sensitive university information is still current before using it in an answer? → A: Revalidate at ingestion and on update-date change or freshness-window expiry; disclose and escalate when freshness cannot be verified.
- Q: What default maximum age should apply when a time-sensitive source does not provide a reliable update date? → A: Never use a time-sensitive source without a reliable update date.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a Verified Answer to a University Question (Priority: P1)

As a prospective student, current student, faculty member, or staff member, I want to ask a university question in natural language and receive a clear answer grounded in approved university information.

**Why this priority**: Reliable answers are the core value of the chatbot and address the primary stakeholder concern about incorrect policy information.

**Independent Test**: Ask a supported question such as how to pay a parking ticket or whether a program is offered, then verify that the response answers the question and identifies the applicable official source.

**Acceptance Scenarios**:

1. **Given** approved current information answers the question, **When** a user asks the question, **Then** the chatbot gives a concise conversational answer and provides the source title, issuing office when available, and source link.
2. **Given** the question depends on campus, term, program, or student status, **When** the user has not supplied that context, **Then** the chatbot asks for the missing context before giving a specific answer.
3. **Given** the answer is general information rather than an official individual determination, **When** the chatbot responds, **Then** it states that limitation without presenting a guarantee.

---

### User Story 2 - Find Multi-Page Policies and Procedures (Priority: P1)

As a student trying to complete a procedure, I want the chatbot to combine relevant information from linked university pages, attached documents, and referenced forms so that I do not have to navigate a chain of links myself.

**Why this priority**: Interviews found that parking, accessibility, policies, and procedures are fragmented across nested pages and documents.

**Independent Test**: Ask how to pay or appeal a parking ticket and verify that the answer includes the applicable steps, linked form or portal, eligibility conditions, and official source references.

**Acceptance Scenarios**:

1. **Given** an approved university page links to relevant child pages or documents, **When** a user asks about the procedure, **Then** the response includes information from the applicable linked material rather than only repeating the top-level page.
2. **Given** a procedure is described in an approved PDF or handbook, **When** a user asks about it, **Then** the chatbot summarizes the relevant section and links to the document.
3. **Given** the source does not contain enough information to complete the procedure, **When** the user asks for the missing step, **Then** the chatbot says it cannot provide a reliable answer and directs the user to the responsible office.

---

### User Story 3 - Get Accurate Dates and Deadline Details (Priority: P1)

As a student, I want registration, add/drop, refund, financial-aid, and academic deadlines presented with the correct term and campus context so that I do not act on an outdated date.

**Why this priority**: Incorrect or stale deadlines can cause direct academic or financial harm.

**Independent Test**: Ask for a deadline from the academic schedule and verify that the response identifies the term, event, date, applicable campus or audience, and source update context.

**Acceptance Scenarios**:

1. **Given** an approved academic schedule lists dates in a table, **When** a user asks for a deadline, **Then** the chatbot preserves the relationship between the event, term, date, and refund or registration condition.
2. **Given** multiple terms or years are present, **When** the user does not identify a term, **Then** the chatbot asks which term is intended instead of selecting one silently.
3. **Given** a date is archived, superseded, or not verifiable as current, **When** a user asks for it, **Then** the chatbot labels the limitation and directs the user to the current official schedule.

---

### User Story 4 - Understand Programs, Courses, and Prerequisites (Priority: P2)

As a prospective or current student, I want a clear summary of programs, course availability, prerequisites, and campus applicability so that I can decide what to investigate or discuss with an advisor.

**Why this priority**: Students reported difficulty finding program offerings and tracing prerequisites across catalog pages, pop-ups, and campus tags.

**Independent Test**: Ask about a program or course and verify that the response combines the relevant catalog details, identifies campus applicability, and distinguishes informational guidance from an official degree audit.

**Acceptance Scenarios**:

1. **Given** course information is distributed across catalog sections, **When** a user asks about prerequisites, **Then** the chatbot presents the relevant prerequisite chain in a single understandable summary.
2. **Given** availability differs between Hammond and Westville, **When** the user asks about course availability without naming a campus, **Then** the chatbot asks which campus applies.
3. **Given** the chatbot cannot verify a program, prerequisite, or offering, **When** the user asks for a definitive answer, **Then** it says “I don’t know” or clearly states that it cannot provide a reliable answer and recommends the appropriate academic office or advisor.

---

### User Story 5 - Escalate Questions the Chatbot Cannot Reliably Answer (Priority: P1)

As a user with a personalized, ambiguous, or unsupported question, I want an honest limitation and a useful contact recommendation rather than an invented answer or a link-only response.

**Why this priority**: Stakeholders explicitly require safe behavior when information is missing, conflicting, outdated, or personalized.

**Independent Test**: Ask an unsupported personalized question, such as resolving a registration error or determining an individual graduation requirement, and verify that the chatbot does not guess and identifies an appropriate university contact path.

**Acceptance Scenarios**:

1. **Given** the chatbot lacks sufficient reliable approved information, **When** the user asks a question, **Then** it says “I don’t know” or that it cannot provide a reliable answer.
2. **Given** approved sources conflict, **When** the chatbot detects the conflict, **Then** it discloses the conflict and directs the user to the responsible university office for confirmation.
3. **Given** the question requires access to private records or an official determination, **When** the user asks for an answer, **Then** the chatbot does not claim to inspect or decide the record and directs the user to the appropriate advisor, registrar, financial-aid office, or other responsible office.

### Edge Cases

- A source page contains repeated navigation, sharing controls, images, expandable content, or buttons that are not part of the policy.
- A linked PDF or child page is unavailable, inaccessible, or has no identifiable publication or update date.
- A table contains multiple campuses, terms, date ranges, refund percentages, or footnotes that change the meaning of a row.
- A catalog lists a prerequisite through several levels of dependent courses.
- A source includes both current and archived versions of a policy.
- A user asks about Purdue University generally when the available approved information applies only to Purdue University Northwest.
- A user asks a personalized question that would require portal access, an academic record, or a staff decision.
- Two approved sources provide materially different dates, eligibility rules, or procedures.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chatbot MUST answer supported questions conversationally using only approved university information that is applicable to the question.
- **FR-002**: The chatbot MUST provide source traceability for policy-related answers, including the source title and direct link when available.
- **FR-003**: The chatbot MUST identify or request relevant context such as campus, term, program, audience, and student status before giving a context-dependent answer.
- **FR-004**: The chatbot MUST follow approved links and include relevant child pages, attached PDFs, handbooks, forms, and referenced policy sections when they are necessary to answer the question.
- **FR-005**: The chatbot MUST exclude unrelated page elements such as navigation controls, sharing buttons, duplicate links, and decorative content from the factual answer.
- **FR-006**: The chatbot MUST preserve the meaning of structured academic schedules, including the relationship among term, event, date, campus, refund percentage, and footnotes.
- **FR-007**: The chatbot MUST distinguish current, future, archived, and superseded information and MUST not present an unverified old deadline as current.
- **FR-008**: The chatbot MUST combine fragmented catalog information into a clear summary of program offerings, course prerequisites, semester availability, and campus tags when those details are available.
- **FR-009**: The chatbot MUST state when an answer is general information and not an official academic, financial, disciplinary, admissions, or degree-audit determination.
- **FR-010**: When sufficient reliable information is unavailable, the chatbot MUST clearly say that it cannot provide a reliable answer and MUST use “I don’t know” when appropriate.
- **FR-011**: When information is missing, conflicting, or personalized, the chatbot MUST direct the user to an appropriate university office or official channel, with a contact link when available.
- **FR-012**: The chatbot MUST not invent policies, deadlines, requirements, exceptions, contacts, program offerings, prerequisites, or procedural steps.
- **FR-013**: The chatbot MUST support questions from prospective students, current students, faculty, and staff within the approved information scope.
- **FR-014**: The chatbot MUST prioritize Purdue University Northwest information for the initial release and MUST clearly identify when a source applies to another Purdue campus or university unit.
- **FR-015**: The chatbot MUST allow a reviewer to determine whether each answer is supported by the cited approved source and applicable context.
- **FR-016**: Every feature change related to this chatbot MUST have clear, reviewable, and testable requirements before implementation begins.
- **FR-017**: The initial chatbot MUST be publicly accessible without sign-in and MUST not use authentication or private account data to answer general questions.
- **FR-018**: The information pipeline MUST revalidate time-sensitive sources at ingestion and when a source update date changes or its configured freshness window expires; if freshness cannot be verified, the chatbot MUST disclose the limitation and escalate rather than present the information as current.
- **FR-019**: The chatbot MUST NOT present time-sensitive information as current unless the source has a reliable update date; undated deadline and schedule sources MUST be escalated instead of used as current.

### Key Entities

- **Approved Source**: An official university webpage, catalog, handbook, policy, schedule, PDF, form, or authorized university communication, with authority and applicability metadata.
- **University Policy Record**: A rule, policy, procedure, requirement, contact instruction, or official guidance extracted from one or more approved sources.
- **Academic Schedule Entry**: A term-specific event with a date, condition, campus or audience scope, and possible refund or registration consequence.
- **Program or Course Record**: An academic offering with campus applicability, prerequisites, semester availability, and related catalog details.
- **User Context**: Information needed to answer safely, including role, campus, term, program, course, and student status.
- **Answer**: A conversational response containing the result, source traceability, context or limitations, and escalation guidance when needed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of evaluated supported policy, procedure, and deadline questions include a correct approved source citation and no unsupported factual claim.
- **SC-002**: At least 90% of evaluated deadline questions return the correct term and date when the user supplies the required campus and term context.
- **SC-003**: At least 90% of evaluated fragmented-procedure questions provide the necessary steps from linked approved pages or documents without requiring the user to manually traverse the source chain.
- **SC-004**: At least 95% of evaluated unsupported, conflicting, or personalized questions explicitly state the limitation and provide an appropriate escalation path instead of guessing.
- **SC-005**: At least 85% of student interview participants can find a source-backed answer to a supported question within 3 minutes.
- **SC-006**: At least 85% of student interview participants rate the answer as clearer and less frustrating than searching multiple PNW pages for the same supported question.
- **SC-007**: Reviewers can independently verify the cited source, applicability context, and answer outcome for 100% of sampled responses.

## Assumptions

- The initial release covers Purdue University Northwest, including Hammond and Westville, rather than every Purdue campus.
- Official PNW webpages, catalogs, schedules, policy repositories, handbooks, and authorized PDFs are the initial approved information scope.
- The chatbot provides information and navigation support; it does not replace advisors, registrars, financial-aid staff, admissions staff, instructors, or official decision processes.
- The initial chatbot is publicly accessible without sign-in and does not access private student records or account data.
- The chatbot does not access private student records or make individualized degree, financial-aid, disciplinary, or admissions determinations.
- University sources may change after they are reviewed; answers must disclose source dates or verification limits when available.
- Time-sensitive sources are revalidated at ingestion and when their update date changes or configured freshness windows expire; sources whose freshness cannot be verified are not presented as current.
- Time-sensitive information without a reliable source update date is not presented as current and is escalated for confirmation.
- Contact information and escalation destinations are included only when they can be verified from approved university sources.
- Performance targets assume ordinary user access and do not define a particular implementation technology.
- The supplied interview notes and URLs are research inputs; they are not authoritative policy sources by themselves.
