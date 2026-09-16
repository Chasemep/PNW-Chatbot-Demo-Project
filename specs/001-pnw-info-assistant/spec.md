# Feature Specification: PNW Student Information & Advising Assistant

**Feature Branch**: `001-pnw-info-assistant`

**Created**: 2026-09-14

**Status**: Draft

**Input**: User description: "Stakeholder interview notes: PNW Dean of Students Office Director Verbal Explanation, Jane's Verbal Explanation (Student Service Coordinator), Student Interviews 1-3, Graduate Student Plan of Study Interview, General Student Interviews on Navigation and Pain Points, Graduation & Scheduling Interview, and Initial Corpus Review Notes (Parking, Academic Schedule tables, Academic Catalog prerequisites, Graduate School Admission, Accessibility, Academic Integrity, Student Handbook PDF, Classroom Behavior Policy PDF, Information Services Policy)."
## Clarifications

### Session 2026-09-16

- Q: How should the assistant handle conversational context across multiple interactions in a student session? → A: Single-turn stateless Q&A (each query is answered in isolation without session memory; ambiguous queries return self-contained composite answers covering all applicable campuses or variations).
- Q: When a student asks for deadline or schedule information without specifying a semester, how should the system determine which academic term to display? (FR-003) → A: Automatic calendar date mapping with upcoming term advance (derive active term from current calendar date; advance to upcoming semester during breaks or after current drop cutoff, explicitly labeling the term).
- Q: How should the system handle student queries that inadvertently contain Personally Identifiable Information (such as a 9-digit PUID / student ID number or personal contact details)? (FR-007) → A: In-flight PII redaction and privacy notice (mask detected student IDs/PII before logging or processing, provide general policy answer with advisor referral, and show a reminder not to share personal IDs).
- Q: How should the system structure and display course prerequisite chains when courses involve alternative course options ('OR' branches), corequisites, or minimum grade cutoffs? (FR-005) → A: Full progressive hierarchy with grade cutoffs and branch logic (present complete dependency sequence from foundational to advanced, explicitly labeling minimum grades, concurrent corequisites, and 'AND'/'OR' choices).
- Q: Should each response include an inline user feedback mechanism (such as thumbs up/down or a "Report outdated info" flag) to help university staff identify inaccurate policies or broken links? → A: Inline binary feedback with optional issue report (thumbs up/down buttons and an optional anonymous "Report outdated info/broken link" text submission on each response).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verified Policy & Procedure Inquiries with Source Grounding (Priority: P1)

As a PNW student, I want to ask plain-language questions about university policies, rules, deadlines, and multi-step procedures (such as paying a parking ticket, filing a grade appeal, or submitting a graduation application) and receive a direct, step-by-step answer grounded in official university documents with links to the verified source pages, so that I do not get trapped in loops of nested links or receive conflicting, outdated information.

**Why this priority**: Directly solves the primary student and staff pain point identified across all interviews: students cannot find actionable procedural answers across fragmented websites/PDFs, and staff spend substantial time answering repetitive questions. Crucially, adheres to Constitution Principle I (Grounded Answers) by guaranteeing every policy statement is directly tied to official documentation.

**Independent Test**: Can be tested by asking common procedural policy questions (e.g., "How do I pay a parking citation?", "What are the steps to appeal a final course grade?", "When is the deadline to drop a class for a 100% refund in Fall?"). Delivers value if the system outputs accurate, concise, step-by-step instructions accompanied by direct links to the official PNW source document.

**Acceptance Scenarios**:

1. **Given** a student looking to resolve a parking ticket, **When** they ask "How do I pay my parking ticket?", **Then** the system provides clear, step-by-step payment instructions (including portal/office payment methods and appeal options) along with a link to the official PNW parking regulations page, without requiring the user to navigate through multiple nested pages.
2. **Given** a student asking about academic standing or grade appeals, **When** they inquire about the process and grounds for appeal, **Then** the system outlines the official procedure defined in the PNW Academic Regulations/Dean of Students policies, cites the relevant policy section, and provides the verified contact point for submitting the appeal.
3. **Given** an inquiry about term-specific deadlines (such as add/drop dates, refund percentages, or graduation application deadlines), **When** the student asks for deadlines without specifying a semester, **Then** the system automatically resolves the active term using current calendar date mapping (advancing to the upcoming semester during breaks or after the drop deadline passes) and provides verified dates from the official academic calendar, explicitly noting the academic term to which the dates apply.

---

### User Story 2 - Campus-Specific & Program-Specific Academic Navigation (Priority: P2)

As a current or prospective student, I want to inquire about academic degree offerings, campus locations, and multi-level course prerequisites, specifying whether I attend the Hammond or Westville campus, so that I receive accurate curriculum requirements and avoid scheduling mistakes that could delay my graduation.

**Why this priority**: Student interviews revealed frequent confusion between Hammond and Westville offerings, confusion navigating different colleges (e.g., College of Engineering & Sciences vs. College of Technology), and instances where students took an extra semester due to hidden, multi-level prerequisite chains.

**Independent Test**: Can be tested by querying program availability (e.g., "Does PNW offer a Computer Science PhD program?") and querying prerequisite paths (e.g., "What are all the prerequisites for CS 30200?"). Delivers value if the system clearly clarifies campus availability and provides complete, multi-step prerequisite sequences.

**Acceptance Scenarios**:

1. **Given** a student asking about advanced degree offerings, **When** they ask "Does PNW offer a computer science PhD program?", **Then** the system explicitly clarifies whether that specific degree is offered at PNW (and notes available graduate programs such as the Master of Science in Computer Science) rather than returning generic catalog search links.
2. **Given** a course that has different sections or availability by campus, **When** a student inquires about course availability or prerequisites, **Then** the system clarifies campus context (Hammond vs. Westville) when requirements or offerings diverge.
3. **Given** an inquiry about course sequencing, **When** a student asks for prerequisites of an advanced course, **Then** the system displays the complete prerequisite chain (including foundational courses required for intermediate courses) in a progressive hierarchical format with explicit annotations for minimum letter grades (e.g., "C or better"), concurrent corequisites, and 'AND'/'OR' pathway choices.

---

### User Story 3 - Fail-Safe Routing & Human Advisor Escalation (Priority: P3)

As a student facing an unanswerable question, personal account error (e.g., registration PIN issue, degree audit hold), or ambiguous situation, I want the system to clearly acknowledge when it cannot reliably answer and immediately provide me with the exact office, department, advisor contact information, and physical/email address to contact, so that I never act on unverified assumptions or false information.

**Why this priority**: Adheres to Constitution Principle II (Fail Safely). Stakeholders (Dean of Students and Coordinator Jane) emphasized that the system must never hallucinate or guess policy details. When an issue is personalized or outside the knowledge base, safe routing prevents student harm and academic delays.

**Independent Test**: Can be tested by submitting ungrounded queries, private account questions ("Why is my registration hold active?"), or complex edge cases. Delivers value if the system gracefully declines to guess and routes the user to the correct university department (Registrar, Bursar, Financial Aid, Dean of Students, or Department Academic Advising).

**Acceptance Scenarios**:

1. **Given** a student encountering a specific registration system error or requesting a private scheduling PIN, **When** they paste their registration error or ask for their PIN, **Then** the system clearly explains that individualized student records and PINs cannot be accessed by the assistant, and directs the student to their designated academic advisor and the Office of the Registrar with contact details and office hours.
2. **Given** a user query where official documentation is conflicting, ambiguous, or absent, **When** the system processes the question, **Then** the system states "I do not have sufficient verified university policy information to answer this reliably" and provides the official contact info for the relevant administrative office.

---

### User Story 4 - Graduate Student Milestone & Plan of Study Guidance (Priority: P4)

As a graduate student, I want step-by-step procedural guidance on graduate-specific milestones (such as drafting and submitting a Master's Plan of Study, committee approvals, and graduate school admission policies), so that I understand required departmental approvals and deadlines without having to piece together contradictory departmental pages.

**Why this priority**: Specific student interview highlighted graduate students struggling to navigate course selection, advisor approval sequences, and submission deadlines for graduate Plans of Study across disconnected departmental and Graduate School portals.

**Independent Test**: Can be tested by asking "How do I submit my plan of study for the Master's in Computer Science?". Delivers value if the assistant outlines the step-by-step workflow (course selection criteria, advisor approval step, Graduate School portal submission, and typical deadlines).

**Acceptance Scenarios**:

1. **Given** a graduate student preparing their Plan of Study, **When** they ask how to complete and submit it, **Then** the system provides the required sequence (drafting courses, securing academic advisor review, electronic submission, and final department sign-off) and provides links to the official forms and graduate school policy.

---

### Edge Cases

- **Contradictory or Outdated Documents**: When two ingested university sources present conflicting rules or deadlines (e.g., an archived handbook vs. current academic calendar), the system must prioritize the current academic calendar/official policy repository and refuse to guess if a contradiction cannot be resolved with certainty.
- **Campus Discrepancy**: A policy or service exists at the Hammond campus but not at the Westville campus (or vice-versa). The system must provide a self-contained composite answer explicitly detailing each campus's applicability in a single response without interactive multi-turn disambiguation.
- **Tabular Data Splitting**: Complex deadline tables containing multiple sub-terms (16-week, 8-week Part of Term A, Part of Term B, summer sessions). The system must identify the term part and refund date accurately without scrambling table columns.
- **Unauthenticated vs. Authenticated Boundaries**: When students ask questions requiring personal account inspection (e.g., financial aid balance, personal transcripts, account holds), the assistant must clearly identify the boundary and provide the direct portal link or office contact rather than attempting to provide generic placeholder answers.
- **Inadvertent PII in Queries**: When a student enters a query containing personal identification numbers (e.g., 9-digit PUID, SSN) or sensitive contact details, the system must sanitize and redact the identifier prior to logging or generating answers, provide the relevant general policy or departmental contact, and display a privacy reminder.
- **Out-of-Scope or Non-University Questions**: When users ask questions unrelated to Purdue University Northwest policies, campus life, or procedures, the assistant must politely state its focus on PNW university policies and decline to answer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide answers to student queries that are strictly grounded in approved, ingested PNW university documents and web pages (Constitution Principle I).
- **FR-002**: The system MUST cite the specific official university source (name of document/webpage and active hyperlink) for every policy, procedure, deadline, or rule presented.
- **FR-003**: The system MUST verify that all dates, deadlines, and schedule information are validated against the requested academic term (Fall, Spring, Summer), or automatically resolve the active term based on the current calendar date (advancing to the upcoming term during breaks or once the current term's drop deadlines have passed) and MUST explicitly indicate the applied academic term in the response.
- **FR-004**: The system MUST operate as a single-turn stateless Q&A service. When a user query involves multi-campus distinctions (Hammond vs. Westville) or variable policy options without specifying context, the system MUST provide a self-contained composite answer clearly identifying requirements for each campus or variation.
- **FR-005**: The system MUST present multi-level course prerequisites in a consolidated, progressive hierarchical format displaying full dependency chains from foundational to advanced courses, explicitly labeling minimum required letter grades (e.g., "C or higher"), concurrent corequisites, and 'AND'/'OR' elective branch logic.
- **FR-006**: When official information is unavailable, incomplete, or ambiguous, the system MUST state that it cannot provide a reliable answer and provide the official contact details (office name, email, phone number, and physical office location) for the relevant university office (Constitution Principle II).
- **FR-007**: The system MUST refuse to generate personalized academic advice, registration PINs, or diagnostic troubleshooting for protected student records, and MUST route the user to their academic advisor or the Office of the Registrar. If a query inadvertently includes student Personally Identifiable Information (such as a 9-digit PUID or personal contact info), the system MUST redact the PII before logging or processing and include a privacy notice reminding the user not to submit confidential student identifiers.
- **FR-008**: The system MUST extract and present complete multi-step workflows for high-frequency processes (including parking ticket payment and appeals, grade appeals, adding/dropping courses, graduation application, and graduate plans of study).
- **FR-009**: The system MUST correctly interpret and present information structured within tabular data (e.g., refund schedules, drop dates by course session) preserving column and row relationships.
- **FR-010**: The system MUST support inquiries regarding university rules contained in PDF documents (including Student Handbook, Classroom Behavior Policy) as well as HTML webpages.
- **FR-011**: The system MUST operate as a public, accessible service without requiring student login for general university policy, procedural, and catalog inquiries.
- **FR-012**: The system MUST provide an anonymous, inline feedback mechanism on each response (thumbs up / thumbs down and an optional text input for reporting outdated information or broken links) to support administrative auditing and continuous improvement of policy accuracy.

### Key Entities

- **University Policy / Document**: An official published source of authority (e.g., Student Handbook, Academic Integrity Policy, Parking Regulations, Classroom Behavior Policy). Attributes include title, source URL, version/effective date, department owner, and campus scope (Hammond, Westville, or University-wide).
- **Academic Term & Deadline Schedule**: A structured record of academic dates (Fall, Spring, Summer) including term parts (full term, 1st 8 weeks, 2nd 8 weeks), add/drop deadlines, refund percentages, and withdrawal cutoffs.
- **Course & Prerequisite Chain**: An academic course offering with associated catalog number, title, credits, campus availability, and prerequisite rules (prerequisite courses, corequisites, minimum grade requirements, and departmental consent).
- **Department / Administrative Contact**: An official university entity responsible for specific procedures (e.g., Office of the Registrar, Dean of Students, Financial Aid, Bursar/Student Accounts, Department Advising Centers). Attributes include department name, contact email, phone number, physical campus building/room, and official website URL.
- **Student Inquiry**: The incoming user prompt or question, captured with context (campus preference, academic level, academic term).
- **Response Feedback**: An anonymous record associated with a single-turn query response, capturing a binary sentiment rating (helpful / unhelpful), a timestamp, and an optional user-submitted description flagging inaccurate policy information or broken links.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of policy, deadline, and procedural answers provided by the assistant include verified citations and active links to official PNW sources.
- **SC-002**: 0% unsupported policy statements or hallucinated deadlines generated (100% adherence to Fail Safely and Grounded Answers constitutional principles).
- **SC-003**: Students can obtain answers to common multi-step procedures (e.g., paying a parking ticket, dropping a course) in under 30 seconds, eliminating multi-page link loops.
- **SC-004**: Inquiries requiring campus distinctions (Hammond vs. Westville) correctly distinguish campus-specific rules in 100% of applicable responses.
- **SC-005**: For unanswerable, personalized, or ambiguous queries, 100% of responses direct the user to the correct university department with complete contact information (office name, email/phone, or portal link).
- **SC-006**: Student task completion rate for finding policy and deadline answers improves by at least 50% compared to baseline manual website navigation.
- **SC-007**: 100% of generated responses include an accessible inline feedback component allowing students to rate answers and report broken citations or outdated content anonymously.

## Assumptions

- **Target Audience**: Current students, prospective students, and campus staff at Purdue University Northwest seeking general policy, catalog, and procedural answers.
- **System Scope**: The initial system operates as an unauthenticated informational assistant focused on official, public PNW university information. Private student records (e.g., personal financial aid balance, personal transcripts, registration PINs) are out of scope for direct automated disclosure and are handled via referral to human advisors or student self-service portals.
- **Conversational Architecture**: The assistant operates strictly as a single-turn stateless Q&A interface. No conversational memory or dialogue context is maintained between successive queries.
- **Document Ingestion Baseline**: The initial knowledge base encompasses official PNW web pages and documents identified in the initial corpus review (Academic Catalog, Academic Schedule, Dean of Students Policies, Parking Regulations, Student Handbook, Classroom Behavior Policy, Graduate Admission/Requirements, Accessibility, and Information Services Policies).
- **Language & Availability**: The assistant will be accessible via standard web browsers in English.
- **Governance**: Any updates to policy documentation will follow official university release cycles, and outdated archived pages will be excluded or tagged with validity dates to prevent serving superseded rules.
