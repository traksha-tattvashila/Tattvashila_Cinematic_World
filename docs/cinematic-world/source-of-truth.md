# Tattvashila Cinematic World — Source of Truth

**Status:** `[SCAFFOLD]`
**Version:** 0.1 (scaffold)
**Maintained by:** Founding team

---

> **For AI agents:** Read this document in full before making any architectural,
> product, or UI change to this repository. This is the primary reference for
> all decisions. When this document conflicts with code comments, README files,
> or inline documentation, this document takes precedence.

---

## 1. Identity

### 1.1 What This Is

<!-- PLACEHOLDER
     Authors: Write a precise, 2–3 sentence description of Tattvashila Cinematic World.
     What is it? What does it do? Who is it for?
     Ground it in what is actually built, not in aspiration.
     The PRD currently describes it as a contemplative cinematic editing and
     atmospheric media system. Refine this into a canonical statement.
-->

_Canonical identity statement to be authored by the founding team._

### 1.2 What This Is Not

<!-- PLACEHOLDER
     Authors: Be explicit. What are the anti-identities?
     Known anti-goals from the PRD include: not a social-media video generator,
     does not optimise for stimulation. Expand this into a complete list.
-->

_To be authored by the founding team._

### 1.3 Canonical Name and Terminology

<!-- PLACEHOLDER
     Authors: Establish the exact canonical names for:
     - The product/system
     - Key subsystems (retrieval, archive, pipeline, editor, etc.)
     - Key concepts (contemplative mode, rubric, assembly, etc.)
     Future agents must use these terms consistently.
-->

| Term | Canonical usage | Do not say |
|------|----------------|------------|
| _[to be filled]_ | — | — |

---

## 2. Purpose

### 2.1 Why This Exists

<!-- PLACEHOLDER
     Authors: One or two paragraphs on the founding purpose. What problem does
     this exist to solve? What would be worse in the world without it?
     Do not write aspirational marketing copy. Write honest purpose.
-->

_To be authored by the founding team._

### 2.2 Who It Serves

<!-- PLACEHOLDER
     Authors: Describe the primary user personas with enough specificity that a
     product decision can be evaluated against them.
     Current personas from PRD (refine or replace):
     - The cultural editor
     - The independent essayist
     - The atelier (programmatic use)
-->

_To be refined by the founding team from PRD personas._

### 2.3 Success Criteria

<!-- PLACEHOLDER
     Authors: How do you know this is working well? What does success look
     like for each persona? Keep these observable, not metric-driven.
-->

_To be authored by the founding team._

---

## 3. Core Principles

<!-- PLACEHOLDER
     Authors: State the 5–8 non-negotiable principles that govern all decisions
     in this codebase. Each principle should be specific enough to resolve
     a real product or technical disagreement.

     Known constraints from existing work (to be elevated into principles or rejected):
     - Restrained transitions only (fade, dissolve, crossfade, hard cut)
     - Black-frame pauses as first-class segments
     - Never optimise for stimulation or virality
     - Slow, observational, emotionally mature visual language
     - Grounded in dharma, carried with integrity

     Structure for each principle:
     ### CP[N] — [Name]
     [Statement]
     **Why:** [Rationale]
-->

_Principles to be authored by the founding team._

---

## 4. UX Philosophy

<!-- PLACEHOLDER
     Authors: What does the UX stand for? What does it refuse to do?
     Connect to mobile-first-ux.md and design-system.md for implementation detail.
     This section should state the philosophy; the other docs implement it.

     Known from existing work:
     - Paper-cream palette
     - Restrained typography (Cormorant Garamond + IBM Plex Sans)
     - Slow opacity-only motion
     - No stimulation-oriented interactions
-->

_To be authored. See `design-system.md` and `mobile-first-ux.md` for implementation._

---

## 5. Media Philosophy

<!-- PLACEHOLDER
     Authors: What does this system believe about media — its sourcing, its use,
     its relationship to truth, its relationship to the subject being filmed?
     See media-ethics.md for detailed ethics policy.
     This section states the philosophy; that document implements it.
-->

_To be authored. See `media-ethics.md` for detail._

---

## 6. Technical Principles

### 6.1 Architecture Constraints

<!-- PLACEHOLDER
     Authors: What technical constraints are non-negotiable?
     Known from existing architecture:
     - Backend: FastAPI + SQLAlchemy async + asyncpg (Supabase Postgres)
     - Object storage via Emergent platform (not S3 directly)
     - Supabase connection MUST use Transaction Pooler (port 6543, not 5432)
     - Frontend: React (CRA) + Tailwind + Shadcn primitives
     - Pipeline: Python-native, runnable as standalone CLI
     Elevate real constraints; remove what is merely implementation detail.
-->

_To be authored. See `architecture.md` for full technical reference._

### 6.2 What May Not Be Changed Without Review

<!-- PLACEHOLDER
     Authors: List the parts of the system that require explicit sign-off before
     modification. Examples might include: the rendering pipeline contracts,
     the segment data model, the retrieval ranking threshold, the storage abstraction.
-->

_To be authored by the founding team._

### 6.3 Dependency Philosophy

<!-- PLACEHOLDER
     Authors: What is the policy on adding dependencies?
     What categories of dependency are prohibited?
-->

_To be authored by the founding team._

---

## 7. Mobile-First Philosophy

<!-- PLACEHOLDER
     Authors: What does mobile-first mean for a contemplative cinematic tool?
     This is not standard mobile-first; it has specific implications for a
     slow-cinema editing environment. State the philosophy here.
     See mobile-first-ux.md for implementation.
-->

_To be authored. See `mobile-first-ux.md` for detail._

---

## 8. Archive Philosophy

<!-- PLACEHOLDER
     Authors: How does this system relate to preservation, permanence, and
     institutional memory of films? What is owed to the work that is stored?
     See archive-philosophy.md for detail.
-->

_To be authored. See `archive-philosophy.md` for detail._

---

## 9. AI Usage Boundaries

### 9.1 Where AI Is Used

<!-- PLACEHOLDER
     Authors: Document explicitly where AI is currently used in the system.
     Known from existing code:
     - Scene analysis: Claude Sonnet 4.5 via Emergent (retrieval/scene_analyzer.py)
     - Clip ranking: Claude Sonnet 4.5 via Emergent (retrieval/ranker.py)
     - Narration TTS: OpenAI TTS-1-HD via Emergent (narration.py)
     - Ambient synthesis: pre-generated, not live AI
-->

| Component | AI used | Purpose | Model |
|-----------|---------|---------|-------|
| Scene analyzer | Claude Sonnet 4.5 | Cinematic rubric generation | `claude-sonnet-4-5-20250929` |
| Clip ranker | Claude Sonnet 4.5 | Score and rationale per clip | `claude-sonnet-4-5-20250929` |
| Narration TTS | OpenAI TTS | Voice generation | `tts-1-hd` / `tts-1` |

### 9.2 Where AI Must Not Be Used

<!-- PLACEHOLDER
     Authors: State explicitly where AI may not make decisions unilaterally.
     What must always have a human in the loop?
     What must never be AI-generated (e.g., final editorial selection)?
-->

_To be authored by the founding team._

### 9.3 AI Agent Instructions (for this repository)

When an AI agent works in this codebase, it must:

- Read this document before making architectural or product decisions
- Not introduce terminology inconsistent with Section 1.3 (canonical terms)
- Not add UI patterns that contradict the UX philosophy in Section 4
- Not optimise for engagement metrics — see anti-goals in Section 10
- Not overwrite `[SCAFFOLD]` placeholder sections with invented content
- Log significant decisions to `decision-log.md`
- Prefer restraint over feature addition when in doubt

---

## 10. Anti-Goals

<!-- PLACEHOLDER
     Authors: Be explicit and specific about what this system refuses to become.
     Known anti-goals from the PRD (confirm and expand):
     - A social-media video generator
     - An engagement-optimised tool
     - A system that prioritises stimulation over contemplation
     - A viral content factory
     Add any others the team has rejected in real decisions.
-->

This system explicitly refuses to:

| Anti-goal | Why it matters |
|-----------|---------------|
| _[to be filled]_ | — |

---

## 11. Decision Log References

Significant architectural and product decisions are recorded in
`docs/cinematic-world/decision-log.md`.

Before proposing a change that touches core behaviour, check the decision log
for context on why the current approach was chosen.

---

## 12. Document Relationships

| Question | Where to look |
|----------|--------------|
| How does the editor look and feel? | `design-system.md`, `mobile-first-ux.md` |
| How are clips retrieved and ranked? | `retrieval-principles.md` |
| How are films stored and preserved? | `archive-philosophy.md` |
| What are the media sourcing rules? | `media-ethics.md` |
| What is the full technical architecture? | `architecture.md` |
| Why was X decided? | `decision-log.md` |
| What does Tattvashila believe? | `../tattvashila/philosophy.md` |

---

## Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-05-15 | 0.1 | Initial scaffold created |
