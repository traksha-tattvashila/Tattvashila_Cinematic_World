# Decision Log

**Status:** `[STABLE]` — this log is always current by definition.

> A chronological record of significant architectural, product, and design
> decisions made during the development of Tattvashila Cinematic World.
> Each entry explains what was decided, why, and what was rejected.
>
> **AI agents:** Before proposing a change, check this log. If a similar change
> was previously considered and rejected, the reason is recorded here.

---

## How to Write a Decision Entry

Each entry should include:

- **Date** — when the decision was made (not when it was recorded)
- **Area** — which part of the system is affected (e.g., `retrieval`, `UX`, `storage`, `schema`)
- **Decision** — what was decided, stated precisely
- **Rationale** — why this was chosen over alternatives
- **Rejected alternatives** — what was considered and not chosen, and why
- **Consequences** — what this decision enables or forecloses
- **Author** — who made the decision (or "team" if collective)

Do not use this log to record obvious implementation choices.
Record only decisions that:
- Were genuinely uncertain
- Had meaningful alternatives
- Will not be obvious to future contributors without explanation
- Were made under constraints that may no longer be apparent later

---

## Log

---

### D001 — Supabase Postgres via Transaction Pooler Only

**Date:** 2026-05-14
**Area:** Infrastructure / Database
**Decision:** All Supabase Postgres connections must use the Transaction Pooler
on port 6543, not the direct connection on port 5432.

**Rationale:** Direct connections (port 5432) fail with IPv4 errors in the Replit
deployment environment. The Transaction Pooler (pgbouncer) is the only
reliable path. Additionally, `statement_cache_size=0` and
`prepared_statement_cache_size=0` are required for pgbouncer compatibility
with asyncpg.

**Rejected alternatives:**
- Direct connection (5432) — fails in this environment
- PgBouncer self-hosted — unnecessary complexity given Supabase provides it

**Consequences:**
- `DATABASE_URL` must always point to the Transaction Pooler endpoint
- Any new database connection code must set the cache parameters above
- Alembic migrations use a separate sync driver (psycopg2) with the same URL

**Author:** Team (v0.4)

---

### D002 — Emergent Object Storage Over Direct S3

**Date:** 2026-05-14
**Area:** Infrastructure / Storage
**Decision:** All media objects (clips, renders, narration, ambient) are stored
via Emergent Object Storage rather than a direct S3 or Supabase storage integration.

**Rationale:** The Emergent platform provides unified object storage accessible
via the same EMERGENT_LLM_KEY used for AI calls. This reduces the number of
credentials required and keeps the storage and AI layers on a single platform
for this stage of development.

**Rejected alternatives:**
- Supabase Storage — would require separate credentials and SDK; deferred
- AWS S3 directly — more flexible but adds credential and IAM complexity

**Consequences:**
- `storage.py` is the sole storage abstraction; all file I/O must go through it
- Storage key is session-scoped and re-initialised on 403 errors
- Vendor dependency on Emergent platform for all stored media

**Author:** Team (v0.1)

---

### D003 — Retrieval Ranking Threshold at 0.55 (Contemplative Mode)

**Date:** 2026-05-14
**Area:** Retrieval
**Decision:** Clips scoring below 0.55 on the LLM ranking scale are hard-excluded
in Contemplative Mode.

**Rationale:** A threshold below 0.55 admitted clips that were cinematically
inappropriate (busy, commercial, stimulation-oriented) even when the search
query was well-formed. 0.55 was the lowest value that reliably excluded these
while still returning enough candidates for assembly.

**Rejected alternatives:**
- Lower threshold (0.4–0.5) — too permissive; admitted visually inappropriate clips
- Higher threshold (0.65+) — too restrictive; too often returned zero candidates
- Soft threshold (warn rather than exclude) — defeated the purpose of the mode

**Consequences:**
- Retrieval may return zero clips if the provider pool is thin
- The threshold is hardcoded in `retrieval/ranker.py`; change requires review
- Any future "non-Contemplative Mode" would need its own threshold policy

**Author:** Team (v0.2)

---

### D004 — No Translate/Scale/Rotate Animations in UI

**Date:** 2026-05-14
**Area:** Frontend / UX
**Decision:** All UI animations are limited to opacity transitions.
No translate, scale, rotate, or spring-physics animations in the editor.

**Rationale:** The contemplative aesthetic requires a still, unhurried interface.
Motion that involves spatial displacement (translate, scale) creates a sense
of urgency or liveliness that contradicts the editorial environment.
Opacity fades are sufficient for state transitions and preserve visual calm.

**Rejected alternatives:**
- Standard CSS transitions with translate — felt too active for the aesthetic
- Framer Motion with spring physics — rejected as too playful
- No animation at all — felt too abrupt for state changes

**Consequences:**
- All `transition-*` classes in Tailwind must be opacity-only
- New components may not introduce translate/scale animations without explicit review
- Loading states must use opacity rather than spinner motion

**Author:** Team (v0.1)

---

### D005 — Black-Frame Pauses as First-Class Segments

**Date:** 2026-05-14
**Area:** Pipeline / Data Model
**Decision:** Silence and black frames are first-class segment types in the
timeline data model, not a post-processing effect.

**Rationale:** In slow cinema, pause is as compositionally significant as footage.
Treating pauses as post-processing would make them invisible to the timeline
and unable to be precisely controlled. First-class treatment means they have
explicit duration, position, and transition properties.

**Rejected alternatives:**
- Post-processing silence insertion — opaque, not editable per segment
- Default fade-to-black at transitions — too automatic; removes editorial control

**Consequences:**
- `segment.kind = "pause"` is a valid segment type throughout the pipeline
- The renderer explicitly handles pause segments (black frame generation)
- Provenance records include pause segments in the timeline

**Author:** Team (v0.1)

---

### D006 — Git History Purge: Credentials Removed from All Commits

**Date:** 2026-05-15
**Area:** Security / Repository
**Decision:** `backend/.env`, `frontend/.env`, and `test_reports/prototype/run.log`
were removed from all git history using `git filter-repo`. All commit SHAs
were rewritten.

**Rationale:** The files were committed in the initial commit and pushed to GitHub
`origin/main`. The credentials (MONGO_URL, DATABASE_URL, EMERGENT_LLM_KEY,
PEXELS_API_KEY, PIXABAY_API_KEY) were treated as compromised.

**Consequences:**
- All historical commit SHAs are different from those on the GitHub remote
- A force-push to `origin/main` is required before the remote history is clean
- All exposed credentials must be rotated before force-push
- `.gitignore` has been updated to prevent recurrence
- A pre-commit hook (``.githooks/pre-commit``) is now in place

**Author:** Replit Agent (security remediation, 2026-05-15)

---

## Decision: Tattvashila and Traksha Separation

### Summary

Tattvashila remains the parent philosophical ecosystem.

Traksha functions as the digital backbone and infrastructure layer.

Tattvashila Cinematic World remains a specialized cinematic/media infrastructure layer.

---

### Reasoning

Separating ecosystem layers prevents:

- architectural overlap
- terminology confusion
- conceptual fragmentation
- uncontrolled scope expansion

This preserves clarity between:

- philosophy
- infrastructure
- cinematic systems

---

### Long-Term Implications

Future contributors and AI agents can work on cinematic systems without unintentionally redefining broader ecosystem architecture.

---

## Decision: Cinematic World Is Not a Generic Video Editor

### Summary

The platform is being developed as cinematic infrastructure rather than a traditional editing application.

---

### Reasoning

The goal is to support:

- cinematic thinking
- narrative construction
- contemplative workflows
- archive intelligence
- emotional continuity
- truth-oriented media systems

rather than generic editing complexity.

---

### Long-Term Implications

The product direction remains meaning-centered rather than feature-chaos oriented.

---

## Decision: Device-Adaptive UX Instead of Responsive Shrinkage

### Summary

The platform should provide native-feeling experiences across:

- mobile
- tablet
- desktop

instead of compressing desktop interfaces onto smaller screens.

---

### Reasoning

Different devices support different cinematic workflows.

Mobile should feel focused and touch-native.

Tablet should feel immersive.

Desktop should feel expansive and workstation-oriented.

---

### Long-Term Implications

Future UX architecture must remain adaptive rather than purely responsive.

---

## Decision: Readability Before Visual Novelty

### Summary

Readability and long-session comfort have higher priority than stylistic experimentation.

---

### Reasoning

Creative systems fail when interfaces create:

- eye fatigue
- cognitive overload
- navigation friction
- visual instability

The platform should support calm cinematic thinking.

---

### Long-Term Implications

Future UI systems must preserve:

- typography clarity
- spacing stability
- visual hierarchy
- low-noise interfaces

---

## Decision: Semantic Systems Over Folder-Heavy Systems

### Summary

The platform should increasingly evolve toward semantic retrieval and archive intelligence.

---

### Reasoning

Traditional folder-heavy media organization becomes limiting at scale.

Semantic systems improve:

- emotional retrieval
- contextual discovery
- narrative continuity
- cinematic memory

---

### Long-Term Implications

Future archive and retrieval systems should prioritize contextual relationships over mechanical categorization.

---

## Decision: Retrieval Is Narrative Infrastructure

### Summary

Retrieval is treated as part of storytelling rather than isolated stock-media search.

---

### Reasoning

Clip discovery directly affects:

- emotional continuity
- pacing
- atmosphere
- movement transitions
- cinematic rhythm

Retrieval should strengthen narrative construction.

---

### Long-Term Implications

Future retrieval systems may evolve toward:

- semantic ranking
- atmospheric continuity scoring
- movement-aware retrieval
- emotional compatibility systems

---

## Decision: Calm Interfaces Over Engagement Optimization

### Summary

The platform should avoid dopamine-driven interface patterns.

---

### Reasoning

Human attention should not be treated as a resource to exploit.

The interface should preserve:

- calmness
- focus
- contemplative pacing
- emotional stability

---

### Long-Term Implications

Future UX systems should avoid:

- addictive loops
- notification-heavy behavior
- overstimulating interfaces
- engagement-maximization patterns

---

## Decision: AI Assists Rather Than Replaces

### Summary

AI systems remain assistive rather than authoritative.

---

### Reasoning

AI may support:

- retrieval
- semantic grouping
- narration workflows
- archive intelligence

But cinematic meaning and ethical responsibility remain human-centered.

---

### Long-Term Implications

Future AI systems should preserve:

- transparency
- creator authorship
- human intentionality
- ethical clarity

---

## Decision: Documentation as Source of Truth Infrastructure

### Summary

Documentation is treated as foundational infrastructure rather than secondary reference material.

---

### Reasoning

Future developers and AI agents require stable philosophical and architectural alignment.

The `/docs` system becomes the canonical reference layer.

---

### Long-Term Implications

Future architectural, cinematic, UX, retrieval, and archive decisions should remain aligned with documented principles.

---

## Decision: Truth-Oriented Media Direction

### Summary

The platform should support truthful and contextually responsible cinematic systems.

---

### Reasoning

Media systems increasingly optimize for manipulation and engagement extraction.

Tattvashila Cinematic World should support:

- truthful storytelling
- documentary integrity
- contextual preservation
- ethical cinematic construction

---

### Long-Term Implications

Future systems may evolve toward:

- truth-first documentary infrastructure
- provenance-aware archives
- contextual lineage systems
- ethical retrieval frameworks

---

# Future Decision Entries

Future entries should follow this structure:

```md
## Decision: [Title]

### Summary

### Reasoning

### Tradeoffs

### Long-Term Implications

### Related Systems

<!-- 
     TEMPLATE FOR NEW ENTRIES — copy and fill in:

### D[NNN] — [Short title]

**Date:** YYYY-MM-DD
**Area:** [retrieval | UX | storage | schema | pipeline | security | infrastructure]
**Decision:** [What was decided, stated precisely.]

**Rationale:** [Why this was chosen.]

**Rejected alternatives:**
- [Alternative 1] — [why rejected]
- [Alternative 2] — [why rejected]

**Consequences:** [What this enables or forecloses.]

**Author:** [Name or "team"]

---
-->
