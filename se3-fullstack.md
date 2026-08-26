# SE3 Fullstack Code Evaluation Criteria

> **Reverse-engineered from an actual Fullstack SE3 evaluation report**
>
> This document reconstructs the likely assessment rubric, scoring rules, evidence requirements, report structure, and interview-generation instructions used by the AI Code Evaluation System. The perspective names, weights, criterion names, criterion weights, decision bands, and output structure are confirmed by the supplied report. Detailed score anchors and evaluator instructions are inferred from how the report applied those criteria.

---

## 1. Assessment Purpose

Evaluate a candidate repository for a **Fullstack Developer — Software Engineering Level 3 (SE3)** role.

The assessment must determine whether the candidate can design, implement, test, secure, operate, and deliver a production-capable application across:

- backend services and persistence;
- frontend architecture and user experience;
- build, test, containerisation, deployment, and CI/CD concerns.

The repository is the primary source of truth. Credit must be based on implemented and verifiable evidence, not merely claims in documentation.

The assessment should identify both:

1. demonstrated SE3-level strengths; and
2. production-readiness gaps that should be explored during interview.

---

## 2. Confirmed Top-Level Scoring Model

The assessment contains three perspectives.

| Perspective | Overall weight |
|---|---:|
| CODE BACKEND | 35% |
| CODE FRONTEND | 35% |
| CICD | 30% |
| **Total** | **100%** |

Each perspective receives a score from **0.0 to 10.0**.

### 2.1 Overall score calculation

```text
Overall Score =
    (Backend Perspective Score × 0.35)
  + (Frontend Perspective Score × 0.35)
  + (CICD Perspective Score × 0.30)
```

Example reconstructed from the supplied report:

```text
Backend:  6.3 × 0.35 = 2.205
Frontend: 5.3 × 0.35 = 1.855
CICD:     6.6 × 0.30 = 1.980

Overall = 6.040, displayed as 6.1/10
```

The report may display weighted scores to two decimal places while displaying the final score to one decimal place.

---

## 3. Confirmed Decision Categories

| Decision | Numeric band | Additional condition |
|---|---:|---|
| EXCELLENT | 9.0–10.0 | No Critical issues |
| VERY GOOD | 8.0–8.9 | No Critical issues |
| SOLID | 7.0–7.9 | No Critical issues |
| POTENTIAL WITH GAPS | 6.0–6.9 | **Or any Critical issue is present** |
| CONDITIONAL FAIL | 5.0–5.9 | **Or multiple Critical issues are present** |
| FAIL | Below 5.0 | Does not meet minimum quality standards |
| ERROR | N/A | Score calculation failed or evidence was invalid |

### 3.1 Decision precedence

The decision must not be derived from the numeric score alone.

Apply the following precedence:

1. A score of 9.0–10.0 can only be EXCELLENT when there are no Critical issues.
2. A score of 8.0–8.9 can only be VERY GOOD when there are no Critical issues.
3. A score of 7.0–7.9 can only be SOLID when there are no Critical issues.
4. One Critical issue may cap the decision at POTENTIAL WITH GAPS.
5. Multiple Critical issues may justify CONDITIONAL FAIL, even when the arithmetic score is 6.0 or higher.
6. A severe security, privacy, data-integrity, or deployability defect may justify a stricter decision than the raw score.
7. The final report must explain any decision that differs from the numeric band.

> **Inference:** The supplied report labels a 6.1 submission with eight Critical issues as POTENTIAL WITH GAPS, despite the reference saying multiple Critical issues may result in CONDITIONAL FAIL. This suggests the evaluator retains judgement rather than applying a fully automatic hard cap.

---

## 4. General 0–10 Scoring Scale

Use whole-number criterion scores unless the evaluation system explicitly supports decimals. Perspective scores are weighted averages and may contain one decimal place.

| Score | Interpretation |
|---:|---|
| 0 | Absent — no meaningful evidence exists |
| 1 | Fundamentally deficient or unusable |
| 2 | Major gaps; unsafe or unsuitable for production |
| 3 | Limited implementation with serious weaknesses |
| 4 | Developing; meaningful work exists but important SE3 expectations are unmet |
| 5 | Basic competent foundation with substantial gaps |
| 6 | Generally competent, but not consistently production-ready |
| 7 | Strong implementation meeting most SE3 expectations |
| 8 | Very strong, mature implementation with minor gaps |
| 9 | Excellent, production-grade implementation with exceptional depth |
| 10 | Exemplary; unusually complete, defensible, and operationally mature |

### 4.1 Scoring principles

- Score the repository as submitted.
- Do not award credit for planned, documented, or claimed features that are absent.
- A dependency being present is not evidence that it is configured or used correctly.
- A working happy path does not prove resilience, security, accessibility, or operational readiness.
- Severe defects in a core path must not be averaged away by unrelated strengths.
- Distinguish between **architecture quality** and **production readiness**.
- Distinguish between **candidate defects** and **evaluation-environment limitations**.
- Explain every score with direct repository evidence.

---

# 5. CODE BACKEND Perspective — 35% of Overall Score

## 5.1 Confirmed Backend Criteria

| Criterion | Perspective weight |
|---|---:|
| API Design | 20% |
| Data Handling | 20% |
| Backend Security | 10% |
| Code Quality | 20% |
| Observability & Monitoring | 10% |
| Reliability & Resilience | 20% |
| **Total** | **100%** |

### Backend perspective calculation

```text
Backend Score =
    (API Design × 0.20)
  + (Data Handling × 0.20)
  + (Backend Security × 0.10)
  + (Code Quality × 0.20)
  + (Observability & Monitoring × 0.10)
  + (Reliability & Resilience × 0.20)
```

---

## 5.2 API Design — 20%

### Evaluate

- REST or RPC semantics appropriate to the use case;
- resource naming and endpoint consistency;
- correct HTTP methods and status codes;
- request and response DTOs;
- validation;
- pagination, sorting, and filtering;
- consistent error contracts;
- API versioning and deprecation strategy;
- OpenAPI or equivalent documentation;
- idempotency for mutation endpoints;
- backward compatibility and consumer impact.

### Score anchors

**0–2:** Endpoints are missing, unusable, unsafe, or fundamentally inconsistent. Core failures return misleading success responses.

**3–4:** Happy-path API works, but contracts, status codes, validation, documentation, pagination, or error handling are materially inconsistent.

**5–6:** Generally sound API design with appropriate contracts and validation; some production or documentation gaps remain.

**7–8:** Strong, consistent, well-documented API design with explicit versioning, error semantics, idempotency, and consumer-focused contracts.

**9–10:** Exemplary API governance, compatibility strategy, complete contract testing, and mature operational semantics.

---

## 5.3 Data Handling — 20%

### Evaluate

- schema design and normalisation;
- data ownership and module boundaries;
- constraints, foreign keys, and unique keys;
- transaction boundaries;
- concurrency handling;
- query design and performance;
- indexes aligned with access patterns;
- migration safety and reversibility;
- bulk operations;
- caching correctness and invalidation;
- consistency between domain model and persistence;
- safe handling of sensitive data;
- evidence of query-plan or load awareness.

### Score anchors

**0–2:** Data design risks corruption, leakage, destructive migrations, or severe scalability failures.

**3–4:** Basic persistence works, but important constraints, transaction semantics, query efficiency, or migration safety are missing.

**5–6:** Competent schema and persistence patterns with reasonable constraints and transactions, but limited evidence of performance engineering.

**7–8:** Strong domain-aligned data model, safe migrations, explicit transaction boundaries, indexing, bulk handling, and defensible caching.

**9–10:** Exceptional data architecture with measured query performance, advanced concurrency handling, migration discipline, and clear operational controls.

---

## 5.4 Backend Security — 10%

### Evaluate

- authentication and authorisation;
- password hashing and credential handling;
- JWT/session lifecycle, expiry, revocation, and rotation;
- role and resource-level access control;
- tenant isolation;
- secrets externalisation;
- encryption and sensitive-data minimisation;
- injection prevention;
- rate limiting and abuse protection;
- security headers where backend-controlled;
- audit logging;
- dependency vulnerabilities.

### Score anchors

**0–2:** Hardcoded credentials, broken authentication, cross-user access, injection vulnerabilities, or severe sensitive-data exposure.

**3–4:** Authentication exists, but authorisation, key management, rate limiting, or sensitive-data handling has important gaps.

**5–6:** Sound baseline security with some missing enterprise controls.

**7–8:** Mature defence-in-depth, secure credential lifecycle, strong authorisation, sensitive-data minimisation, and abuse controls.

**9–10:** Exemplary enterprise security with key rotation, comprehensive auditability, automated scanning, and clearly reasoned threat controls.

---

## 5.5 Backend Code Quality — 20%

### Evaluate

- architecture and module boundaries;
- SOLID principles and dependency direction;
- cohesion and coupling;
- naming and consistency;
- type safety;
- validation consistency;
- duplication and dead code;
- error handling;
- framework-appropriate patterns;
- testability;
- unnecessary abstraction or overengineering;
- language-specific correctness;
- comments and documentation where decisions are non-obvious.

### Score anchors

**0–2:** Code is difficult to follow, tightly coupled, unsafe, or contains fundamental language/framework mistakes.

**3–4:** Some structure exists, but inconsistency, duplication, incorrect abstractions, or weak error handling materially harms maintainability.

**5–6:** Generally maintainable and testable code with defensible structure; several quality improvements remain.

**7–8:** Strong architecture, clear boundaries, consistent style, good abstractions, and high change safety.

**9–10:** Exemplary engineering structure, enforced architectural rules, unusually clear design, and excellent evolvability.

---

## 5.6 Observability & Monitoring — 10%

### Evaluate

- structured application logging;
- correlation or trace IDs;
- propagation through asynchronous/reactive flows;
- useful context fields and safe redaction;
- metrics;
- health, liveness, and readiness indicators;
- dependency health;
- tracing;
- alertability;
- error and latency visibility;
- operational dashboards;
- production diagnostics.

### Score anchors

**0–2:** Little or no useful logging, no health visibility, and production incidents would be extremely difficult to diagnose.

**3–4:** Basic logs or framework health endpoints exist, but correlation, structure, dependency health, metrics, or actionable context is missing.

**5–6:** Competent operational visibility with logs, metrics, and health endpoints; some tracing or diagnostic depth is absent.

**7–8:** Strong structured observability, request correlation, custom dependency indicators, dashboards, and actionable metrics.

**9–10:** Comprehensive observability with distributed tracing, SLO-aligned alerting, redaction controls, and clear incident workflows.

---

## 5.7 Reliability & Resilience — 20%

### Evaluate

- database connection pooling and limits;
- client and server timeouts;
- retries with backoff and jitter;
- circuit breakers;
- bulkheads and concurrency controls;
- graceful degradation;
- fail-open versus fail-closed decisions;
- idempotency;
- duplicate and replay handling;
- partial failure behaviour;
- graceful shutdown;
- resource cleanup;
- external dependency failure handling;
- load and saturation behaviour;
- startup ordering and recovery.

### Score anchors

**0–2:** Core flows fail unsafely, no operational safeguards exist, or the service is likely to collapse under ordinary production failure/load conditions.

**3–4:** Some resilience patterns exist, but important dependencies lack timeouts, retries, pooling, circuit breaking, or correct failure semantics.

**5–6:** Reasonable production baseline with explicit timeouts, pooling, idempotency, and recoverable failures; some gaps remain.

**7–8:** Mature resilience design with bounded resources, deliberate retry/circuit-breaker policies, graceful degradation, and tested failure handling.

**9–10:** Exceptional reliability engineering supported by load tests, chaos/failure tests, measured limits, and clear recovery procedures.

---

# 6. CODE FRONTEND Perspective — 35% of Overall Score

## 6.1 Confirmed Frontend Criteria

| Criterion | Perspective weight |
|---|---:|
| Component Design | 25% |
| UI/UX Implementation | 20% |
| Frontend Security | 10% |
| Code Quality | 25% |
| Reliability & Resilience | 20% |
| **Total** | **100%** |

### Frontend perspective calculation

```text
Frontend Score =
    (Component Design × 0.25)
  + (UI/UX Implementation × 0.20)
  + (Frontend Security × 0.10)
  + (Code Quality × 0.25)
  + (Reliability & Resilience × 0.20)
```

> **Confirmed report behaviour:** Frontend test absence was considered under Frontend Reliability & Resilience and again under the CICD Test Coverage & Quality criterion. This is permitted because the perspectives assess different consequences: runtime/change safety versus delivery quality assurance.

---

## 6.2 Component Design — 25%

### Evaluate

- component boundaries and responsibilities;
- page, feature, layout, and shared-component structure;
- composition versus inheritance;
- prop design and type safety;
- reusable abstractions;
- form architecture;
- state ownership;
- context/provider usage;
- separation of server state and UI state;
- role-based routing and layouts;
- avoidance of oversized components;
- coupling to API details.

### Score anchors

**0–2:** Components are monolithic, tightly coupled, duplicated, or unsuitable for extension.

**3–4:** Basic modularity exists, but state ownership, component boundaries, or reuse patterns are inconsistent.

**5–6:** Competent feature structure and typed components with reasonable separation of concerns.

**7–8:** Strong component architecture with clear feature boundaries, deliberate state ownership, composability, and scalable patterns.

**9–10:** Exemplary frontend architecture with highly coherent components, excellent evolvability, and enforced design conventions.

---

## 6.3 UI/UX Implementation — 20%

### Evaluate

- completion of user journeys;
- visual and interaction consistency;
- loading, empty, success, and failure states;
- validation feedback;
- responsive behaviour;
- keyboard navigation;
- semantic HTML;
- ARIA usage;
- focus management;
- screen-reader announcements;
- accessibility against WCAG expectations;
- user recovery from failures;
- perceived performance;
- search, pagination, and large-data usability.

### Score anchors

**0–2:** Core journeys are unusable, inaccessible, misleading, or frequently crash.

**3–4:** Basic UI works, but important feedback, accessibility, responsiveness, or recovery states are missing.

**5–6:** Functional, understandable UI with reasonable feedback and baseline accessibility; several refinements remain.

**7–8:** Strong UX with deliberate state handling, accessibility, keyboard support, responsiveness, and polished error recovery.

**9–10:** Exceptional, inclusive user experience supported by accessibility testing and carefully designed interaction behaviour.

---

## 6.4 Frontend Security — 10%

### Evaluate

- token/session storage choices;
- logout and revocation behaviour;
- XSS exposure;
- unsafe HTML rendering;
- sensitive data in browser storage or logs;
- route protection versus actual server authorisation;
- CSP and security headers;
- CSRF considerations;
- CORS assumptions;
- secrets embedded in frontend builds;
- dependency vulnerabilities;
- URL/query-string leakage;
- clickjacking protection where applicable.

### Score anchors

**0–2:** Secrets or sensitive tokens are exposed, unsafe rendering exists, or the client relies on cosmetic route protection for security.

**3–4:** Reasonable basics exist, but CSP, storage, logout, XSS controls, or security headers have significant gaps.

**5–6:** Competent baseline with safe token handling and no obvious critical browser-side vulnerabilities.

**7–8:** Strong browser security posture with CSP, secure session strategy, dependency controls, and deliberate threat handling.

**9–10:** Exemplary frontend security with automated checks, hardened delivery configuration, and clearly documented threat decisions.

---

## 6.5 Frontend Code Quality — 25%

### Evaluate

- TypeScript strictness and meaningful typing;
- naming and consistency;
- linting and formatting;
- duplication and dead code;
- API client design;
- error-model consistency;
- state-management clarity;
- side-effect management;
- hooks correctness;
- cancellation and stale-request handling;
- comments, debug code, and production cleanliness;
- maintainability and testability.

### Score anchors

**0–2:** Weak typing, tangled state, pervasive duplication, unsafe effects, or code that is difficult to maintain.

**3–4:** Some quality controls exist, but inconsistent patterns, debug remnants, weak error handling, or fragile state logic remain.

**5–6:** Generally clean and typed frontend with reasonable conventions and maintainability.

**7–8:** Strong TypeScript, clear API/state patterns, consistent tooling, and highly maintainable feature code.

**9–10:** Exemplary frontend engineering with excellent static guarantees, enforced conventions, and outstanding clarity.

---

## 6.6 Frontend Reliability & Resilience — 20%

### Evaluate

- root and feature-level error boundaries;
- API request timeouts;
- cancellation using AbortController or equivalent;
- retry policy and exponential backoff;
- distinction between retryable and non-retryable failures;
- duplicate submission protection;
- idempotency-key behaviour;
- offline/network instability handling;
- stale request and race-condition handling;
- optimistic update rollback;
- loading and retry UX;
- client-side error tracking;
- code splitting and lazy loading;
- performance under slow networks;
- frontend automated tests where relevant to runtime confidence.

### Score anchors

**0–2:** A component error can crash the entire application, network failures are unrecoverable, and no automated safety net exists.

**3–4:** Some defensive handling exists, but error boundaries, timeouts, retries, cancellation, or client monitoring are materially incomplete.

**5–6:** Competent runtime resilience with recoverable errors, sensible request handling, and basic performance safeguards.

**7–8:** Strong failure isolation, retry/cancellation strategy, client monitoring, tested idempotency, and deliberate performance optimisation.

**9–10:** Exceptional resilience across component, network, state, and browser failure modes with measured performance and extensive failure-path tests.

---

# 7. CICD Perspective — 30% of Overall Score

## 7.1 Confirmed CICD Criteria

| Criterion | Perspective weight |
|---|---:|
| Build Quality & Configuration | 27% |
| Test Coverage & Quality | 36% |
| CI/CD Pipeline & Automation | 5% |
| Deployment Readiness | 22% |
| Developer Experience & Documentation | 10% |
| **Total** | **100%** |

### CICD perspective calculation

```text
CICD Score =
    (Build Quality & Configuration × 0.27)
  + (Test Coverage & Quality × 0.36)
  + (CI/CD Pipeline & Automation × 0.05)
  + (Deployment Readiness × 0.22)
  + (Developer Experience & Documentation × 0.10)
```

---

## 7.2 Build Quality & Configuration — 27%

### Evaluate

- reproducible builds;
- build-tool wrappers;
- lock files and pinned versions;
- dependency management;
- multi-stage container builds;
- runtime image minimisation;
- non-root execution;
- Docker layer efficiency;
- environment consistency;
- static analysis;
- linting and formatting;
- coverage tooling;
- software-composition and vulnerability scanning;
- build warnings and errors;
- frontend bundle optimisation;
- toolchain version consistency.

### Score anchors

**0–2:** Builds are missing, irreproducible, or fail under normal setup.

**3–4:** Build works but lacks locking, consistency, security tooling, or sound container practices.

**5–6:** Competent reproducible build with standard quality tooling and usable containers.

**7–8:** Strong, optimised, secure build configuration with comprehensive tooling and consistent environments.

**9–10:** Exemplary build engineering with measured performance, hermetic/reproducible practices, SBOM/signing, and rigorous automated quality controls.

---

## 7.3 Test Coverage & Quality — 36%

### Evaluate

- backend unit tests;
- backend integration tests;
- frontend unit tests;
- frontend component tests;
- end-to-end tests;
- architecture tests;
- contract tests;
- security tests;
- representative test data;
- deterministic execution;
- test isolation;
- infrastructure dependencies;
- separation between fast and slow suites;
- coverage reporting and thresholds;
- failure-path and edge-case coverage;
- whether tests actually execute in the evaluation environment.

### Score anchors

**0:** No automated tests or test framework.

**1–2:** Very limited tests, major application layers untested, or tests are non-executable/unreliable.

**3–4:** Meaningful tests exist but important frontend/backend flows, failure paths, or integration boundaries are absent.

**5–6:** Competent multi-layer test suite with reasonable coverage; one side of the fullstack solution may still be weaker.

**7–8:** Strong balanced testing across backend, frontend, integrations, architecture, and key user journeys with reliable execution.

**9–10:** Exceptional quality engineering with comprehensive functional and non-functional tests, strict gates, contract coverage, mutation/property testing where useful, and highly reliable feedback.

### Evaluation-environment rule

If integration tests fail only because the evaluator environment lacks Docker or another documented external dependency:

- report the failure accurately;
- distinguish infrastructure limitation from candidate defect;
- still assess whether the project provides a fast unit-test path;
- do not claim passing coverage that could not be measured;
- recommend separating fast unit tests from container-dependent integration tests.

---

## 7.4 CI/CD Pipeline & Automation — 5%

### Evaluate

- presence of GitHub Actions, GitLab CI, Jenkins, Azure DevOps, or equivalent;
- automated backend and frontend build;
- automated test execution;
- linting and static analysis;
- coverage and security quality gates;
- image creation and publication;
- environment promotion;
- secret handling;
- branch protection assumptions;
- deployment automation;
- rollback support.

### Score anchors

**0–2:** No pipeline, or only a trivial/manual workflow.

**3–4:** Basic build/test pipeline exists, but quality gates, deployment, or security controls are incomplete.

**5–6:** Competent CI pipeline covering primary build and test paths.

**7–8:** Strong automated pipeline with parallelisation, caching, quality gates, image publication, and safe deployment stages.

**9–10:** Exemplary software-delivery automation with progressive delivery, signed artefacts, policy gates, observability checks, and proven rollback.

> The low 5% weight means pipeline absence should not overwhelm strong engineering evidence, but it remains an SE3 delivery gap and may still be classified as Critical depending on the brief.

---

## 7.5 Deployment Readiness — 22%

### Evaluate

- production container images;
- Docker Compose or equivalent local orchestration;
- externalised configuration;
- 12-factor principles;
- secrets management expectations;
- health checks;
- readiness and liveness behaviour;
- database migrations;
- startup order;
- statelessness;
- persistent storage;
- environment profiles;
- horizontal scaling assumptions;
- zero-downtime deployment considerations;
- rollback and recovery;
- resource limits and runtime configuration;
- reverse proxy configuration and headers.

### Score anchors

**0–2:** Application cannot be deployed reliably or has fatal runtime/dependency configuration gaps.

**3–4:** Local deployment works, but production concerns such as health checks, secrets, migrations, or scaling are incomplete.

**5–6:** Competent deployment setup with usable containers, external configuration, and basic operational readiness.

**7–8:** Strong production-oriented deployment design with safe migrations, health semantics, scaling support, and clear environment controls.

**9–10:** Exemplary deployment readiness with tested rollout/rollback, infrastructure automation, resource tuning, and operational runbooks.

---

## 7.6 Developer Experience & Documentation — 10%

### Evaluate

- README setup accuracy;
- architecture overview;
- prerequisite documentation;
- build, test, and run commands;
- environment variable reference;
- seed data and demo accounts;
- API documentation;
- troubleshooting guidance;
- documented limitations;
- development scripts;
- repository organisation;
- onboarding clarity;
- consistency between documentation and implementation.

### Score anchors

**0–2:** Repository cannot be understood or run without substantial undocumented knowledge.

**3–4:** Basic setup documentation exists but is incomplete, inaccurate, or omits key operational details.

**5–6:** Competent documentation enabling a developer to build, test, and run the system.

**7–8:** Strong onboarding and architecture documentation with accurate commands, troubleshooting, and clear decisions.

**9–10:** Exemplary developer experience with automation, ADRs, complete operational guidance, and continuously verified documentation.

---

# 8. Issue Severity Model

The report must count issues by severity:

- Critical
- High
- Medium
- Low

## 8.1 Critical

Use when the issue can reasonably:

- prevent production deployment or cause immediate instability under expected load;
- expose authentication credentials or sensitive data;
- enable unauthorised access;
- corrupt or duplicate important business data;
- make the application broadly unusable;
- eliminate all automated confidence for a critical application layer;
- make failures impossible to detect or recover from;
- produce a serious legal, regulatory, or accessibility exposure.

Examples:

- missing database connection pooling for a production reactive service;
- no frontend tests at all for an SE3 fullstack submission;
- no error boundary where one render error crashes the entire SPA;
- absent customer-level authorisation;
- broken health probes that prevent orchestration;
- missing required CI/CD pipeline when automated delivery is a core requirement.

## 8.2 High

Use for material production, maintainability, security, or scalability risk that does not necessarily make the system immediately unusable.

Examples:

- no rate limiting;
- missing query optimisation for known growth paths;
- incomplete API documentation;
- no custom dependency health indicators;
- no client-side error tracking;
- no code splitting for a meaningful application.

## 8.3 Medium

Use for significant engineering improvements that affect consistency, operability, performance, or developer effectiveness but are not immediate production blockers.

Examples:

- inconsistent validation handling;
- missing key-rotation strategy;
- incomplete structured error contracts;
- toolchain version inconsistency;
- limited deployment documentation.

## 8.4 Low

Use for minor polish, naming, documentation, small inefficiencies, or low-risk cleanup.

### Severity discipline

- Severity must be based on concrete impact, not dramatic wording.
- Do not classify every missing best practice as Critical.
- Explain why the issue has the selected severity.
- Avoid double-counting the same defect as multiple issues unless it creates distinct consequences in different layers.

---

# 9. Repository Inspection and Execution Workflow

The evaluator should perform as much of the following as the environment permits.

## 9.1 Inventory

- identify frontend, backend, infrastructure, and documentation directories;
- identify languages, frameworks, build tools, and package managers;
- inspect lock files and toolchain versions;
- identify tests and CI/CD files;
- inspect Dockerfiles and Compose manifests;
- inspect migrations and configuration;
- inspect security and observability dependencies.

## 9.2 Build execution

Record:

- command;
- duration;
- result;
- warnings;
- errors;
- generated artefacts;
- relevant environment limitations.

Attempt backend and frontend builds independently where practical.

## 9.3 Test execution

Record:

- command;
- duration;
- number run;
- passed;
- failed;
- skipped;
- coverage, when available;
- reason for infrastructure-dependent failures;
- whether frontend tests exist and can execute.

Do not silently omit failed commands.

## 9.4 Static inspection

Search for and inspect:

- authentication and authorisation;
- secret defaults;
- token storage;
- API client behaviour;
- error boundaries;
- retries, timeouts, and circuit breakers;
- connection pools;
- health indicators;
- logging and correlation IDs;
- migrations and query patterns;
- frontend accessibility;
- code splitting;
- test framework configuration;
- CI/CD pipelines;
- production server configuration.

## 9.5 Evidence format

For material findings, include:

```text
relative/path/to/file.ext:lineStart-lineEnd
```

Then provide the smallest relevant code excerpt. Do not include excessive source code.

---

# 10. Required Issue Format

Critical issues should normally contain all of the following sections:

````markdown
**Issue #N: Concise issue title**

```language
// relevant repository excerpt
```

**Problem:**
What is wrong in the submitted implementation.

**Impact:**
- Concrete production, user, security, data, or delivery consequences.

**Solution:**
A technically credible correction, including code only where useful.

**Interview Question:**
> A repository-specific question that tests whether the candidate understands the defect and trade-offs.

**Success criteria:**
- ✅ Specific concepts a strong SE3 answer should cover.

**Failure criteria:**
- ❌ Answers indicating lack of understanding or ownership.
````

High and Medium issues may use a shorter format:

- Problem
- Impact
- Recommendation

### Solution quality rules

- Recommend framework-appropriate patterns.
- Do not present arbitrary constants as universally correct production settings.
- State when values require load testing or environment-specific sizing.
- Distinguish retryable from non-retryable operations.
- Avoid recommending retries for non-idempotent mutations unless idempotency is guaranteed.
- Avoid absolute performance-benefit claims unless measured.

---

# 11. Outstanding Qualities Format

Each perspective should identify meaningful strengths.

Use:

```markdown
**Quality title:** Evidence-based description of the design or implementation.
  - *Impact:* Why this demonstrates SE3 capability or improves production outcomes.
```

Only call a quality “production-grade,” “exceptional,” or “excellent” when supported by repository evidence.

Examples of valid strength areas:

- clean or hexagonal architecture;
- reactive programming used correctly;
- idempotency and duplicate protection;
- safe transaction boundaries;
- sound caching patterns;
- secure password and token handling;
- strong TypeScript configuration;
- component separation;
- comprehensive tests;
- container and build quality;
- architecture enforcement tests.

---

# 12. Key Recommendations Format

For each perspective, produce a prioritised list.

```markdown
1. **Priority 1**: Specific action.
   - *Expected Benefit:* Concrete, defensible outcome.
```

Priorities must address the highest production or quality risks first.

Do not use unsupported numeric claims such as “improves reliability to 99.9%” or “reduces development time by 50%” unless derived from actual measurements. Prefer qualitative or bounded benefits.

---

# 13. Required Report Structure

The final report should follow this structure.

```markdown
# Code Evaluation Report

- **Candidate Name:** <name>
- **Role:** Fullstack Developer
- **Evaluated Level:** Software Engineering Level 3 (SE3)

**Report Generated:** <UTC ISO-8601 timestamp>

---

## 1. Executive Summary

**Overall Score:** X.X/10
**Decision:** **<DECISION>**

**Issue Summary:**
- Critical: N
- High: N
- Medium: N
- Low: N

**Evaluator Comments:**
<balanced summary of capability, major strengths, production gaps, and interview recommendation>

---

## 2. Scores Table

| Perspective | Score | Weight | Weighted Score | Status |
|---|---:|---:|---:|---|
| CODE BACKEND | X.X / 10 | 35% | X.XX | <summary> |
| CODE FRONTEND | X.X / 10 | 35% | X.XX | <summary> |
| CICD | X.X / 10 | 30% | X.XX | <summary> |
| **Overall** | **X.X / 10** | **100%** | **X.XX** | **<DECISION>** |

#### Score Interpretation:
<explain why the score and issue profile produce the decision>

---

## 3. Detailed Evaluations

### 3.1 CODE BACKEND Perspective (X.X / 10)

#### Summary of Findings:
<summary>

#### Scoring Details:
<table of backend criteria, score, weight, reason>

#### Outstanding Qualities
<evidence and impact>

#### Critical Issues
<full issue format>

#### High Issues
<shorter issue format>

#### Medium Issues
<shorter issue format>

#### Key Recommendations:
<prioritised list>

---

### 3.2 CODE FRONTEND Perspective (X.X / 10)

<same pattern>

---

### 3.3 CICD Perspective (X.X / 10)

<same pattern plus build/test execution results>

---

## Decision Rationale

<explain final classification, whether to proceed to interview, and whether gaps appear to be knowledge, prioritisation, or time constraints>

---

*This report was automatically generated by the AI Code Evaluation System*

---

## Decision Categories Reference

<confirmed decision table>
```

---

# 14. Interview Recommendation Rules

The report should recommend one of the following:

- proceed confidently;
- proceed to a targeted interview;
- proceed only for a lower level;
- do not proceed;
- unable to determine due to evaluation error.

A **targeted interview** is appropriate where:

- the candidate demonstrates strong architectural depth but omits production safeguards;
- implementation gaps may plausibly result from assessment time constraints;
- the panel needs to distinguish a knowledge gap from a prioritisation decision;
- one side of the fullstack submission is significantly stronger than the other.

Interview questions must:

- reference the candidate’s implementation;
- ask for runtime consequences, not definitions;
- test trade-offs and recovery paths;
- include success and failure criteria for Critical issues;
- avoid revealing the entire expected answer in the question.

---

# 15. Fullstack SE3 Calibration Principles

A Fullstack SE3 candidate may be stronger in one layer, but must demonstrate credible competence across all three perspectives.

## Strong SE3 signals

- explains complete user-to-database flows;
- anticipates failure modes;
- protects data and access boundaries;
- uses transactions and idempotency correctly;
- writes balanced frontend and backend tests;
- can diagnose production incidents using logs, metrics, and traces;
- creates reproducible builds and automated delivery paths;
- understands accessibility and browser failure modes;
- can justify architectural trade-offs without relying on framework prestige;
- documents limitations honestly.

## Below-SE3 signals

- happy-path implementation without failure handling;
- zero testing on a major application layer;
- no understanding of database saturation or connection pooling;
- unbounded retries or no retries/timeouts at all;
- authentication without resource-level authorisation;
- frontend crashes without isolation or recovery;
- no accessibility consideration;
- manual-only delivery without quality gates;
- production claims unsupported by implementation;
- inability to distinguish evaluator-environment limitations from code defects.

---

# 16. Confirmed Versus Inferred Elements

## High-confidence confirmed

The supplied report directly confirms:

- the three perspectives;
- 35% / 35% / 30% overall weights;
- every criterion name and internal criterion weight;
- the overall weighted-average calculation;
- issue severities and issue counts;
- report section order;
- detailed issue format;
- build/test execution reporting;
- decision category names and numeric bands;
- automatic report attribution;
- use of repository-specific interview questions with success/failure criteria.

## Inferred

The following are reconstructed from how the report behaves:

- detailed 0–10 anchors for each criterion;
- severity definitions;
- decision precedence when multiple Critical issues exist;
- minimum evidence standards;
- exact inspection workflow;
- precise wording of evaluator instructions;
- whether all criterion scores must be integers;
- whether issue severities directly alter scores or only affect the decision.

---

# 17. Evaluation Quality Guardrails

To improve reliability of the generated assessment:

1. Verify framework defaults against primary documentation before declaring a production showstopper.
2. Do not prescribe a specific connection-pool size without workload, query-latency, and database-capacity evidence.
3. Do not retry every database operation indiscriminately.
4. Do not recommend fail-open security behaviour without explicitly analysing the security consequence.
5. Do not call missing client-side retries Critical for every request; mutation retries require idempotency.
6. Do not treat a missing custom health indicator as equivalent to a missing health endpoint.
7. Do not claim WCAG non-compliance solely from absence of ARIA labels; inspect semantic HTML and actual interactions.
8. Do not use unsupported quantitative benefit claims.
9. Distinguish code defects from evaluation-environment limitations.
10. Prefer evidence-based phrasing such as “not demonstrated” over absolute claims when runtime behaviour was not executed.

