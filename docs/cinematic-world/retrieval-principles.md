# Retrieval Principles

**Status:** `[SCAFFOLD]`

> This document defines how Tattvashila Cinematic World approaches the retrieval,
> evaluation, and selection of media clips. Retrieval is not search — it is a
> curatorial act guided by cinematic intention.

---

## 1. What Retrieval Is

<!-- PLACEHOLDER
     Authors: Write a precise definition of what "retrieval" means in this system.
     It is currently: scene analysis → rubric generation → concurrent provider search
     → LLM ranking → threshold filtering → assembly.
     What is the intended relationship between the retrieval system and editorial intent?
-->

_To be authored by the founding team._

---

## 2. The Retrieval Pipeline (Current)

```
User intent / project description
        ↓
Scene Analyzer (Claude Sonnet 4.5)
  → cinematic rubric:
      tone, pacing, environment, atmosphere,
      restraint_level, search_queries,
      preferred_keywords, rejected_keywords, rationale
        ↓
Concurrent provider search
  → Pexels Videos API
  → Pixabay Videos API
  → [Local archive — future]
        ↓
Ranker (Claude Sonnet 4.5)
  → per-clip score (0–1) + one-line rationale
  → heuristic pre-filter on rejected_keywords
  → hard threshold: 0.55 (Contemplative Mode)
        ↓
Ranked clip pool → timeline assembly
```

<!-- PLACEHOLDER
     Authors: Review and correct the above pipeline diagram as the system evolves.
     Add or remove stages. Document the rationale for each stage.
-->

---

## 3. The Cinematic Rubric

The rubric is the core artefact of retrieval. It translates editorial intent into
parameters that guide search and ranking.

### 3.1 Current Rubric Fields

| Field | Type | Purpose |
|-------|------|---------|
| `tone` | string | Emotional register of the scene |
| `pacing` | string | Intended tempo / rhythm |
| `environment` | string | Physical or atmospheric setting |
| `atmosphere` | string | Textural quality sought |
| `restraint_level` | string | How conservative the selection should be |
| `search_queries` | string[] | Provider search terms |
| `preferred_keywords` | string[] | Tags that boost clip score |
| `rejected_keywords` | string[] | Tags that trigger pre-filter disqualification |
| `rationale` | string | Model's explanation of its choices |

### 3.2 Rubric Authorship

<!-- PLACEHOLDER
     Authors: Who or what may author a rubric?
     Currently: Claude Sonnet 4.5 only.
     Future: manual rubric authoring? Partial override?
     What fields may humans override vs. what must remain AI-generated?
-->

_Rubric authorship policy to be authored by the founding team._

---

## 4. Ranking Principles

### 4.1 The Contemplative Mode Threshold

The system applies a hard disqualification threshold of **0.55** in Contemplative Mode.
Clips scoring below this are excluded regardless of query match.

<!-- PLACEHOLDER
     Authors: Document the rationale for 0.55.
     How was this value determined? What does it guard against?
     Under what circumstances may it be lowered?
     Is there a non-Contemplative Mode? What threshold applies?
-->

_Threshold rationale to be authored by the founding team._

### 4.2 What AI Ranking May and May Not Do

<!-- PLACEHOLDER
     Authors: Define the scope and limits of AI involvement in clip selection.
     Currently: AI ranks; human (or assembly logic) makes final selection.
     May the AI reject all clips? What happens then?
     May the AI select a clip the human has explicitly excluded?
-->

_To be authored by the founding team._

### 4.3 Human Override

<!-- PLACEHOLDER
     Authors: Document the current and intended mechanisms for human editorial
     override of retrieval results. Can a user reject a ranked clip?
     Can a user force-include a specific clip? How is this recorded in provenance?
-->

_To be authored by the founding team._

---

## 5. Provider Principles

### 5.1 Current Providers

| Provider | Role | Diversity consideration |
|----------|------|------------------------|
| Pexels | Primary stock source | Western-skewed catalogue |
| Pixabay | Secondary stock source | Broader amateur/creative commons pool |
| Local archive | Future | _[to be defined]_ |

### 5.2 Provider Diversity and Representation

<!-- PLACEHOLDER
     Authors: What obligations does the system have to the diversity of
     representation in retrieved footage? Are there known gaps in current
     providers? Is geographic or cultural diversity a retrieval criterion?
-->

_To be authored by the founding team._

### 5.3 Adding or Removing Providers

<!-- PLACEHOLDER
     Authors: What criteria must a new provider meet to be added?
     What would cause an existing provider to be removed?
     Who makes this decision?
-->

_To be authored by the founding team._

---

## 6. Retrieval Failure Modes

<!-- PLACEHOLDER
     Authors: Document known failure modes and how they are handled:
     - No clips meet the threshold → what happens?
     - Provider API is unavailable → fallback behaviour?
     - Rubric generation fails → does assembly proceed?
     - Clips retrieved but assembly yields unsatisfying result → any recourse?
-->

_To be authored from operational experience._

---

## 7. Future Expansion Areas

<!-- PLACEHOLDER
     Authors: Note retrieval capabilities that are architecturally planned
     but not yet implemented. Do not make commitments here — note possibilities.
     Known placeholder from PRD: local archive provider.
-->

- Local / institutional archive as a retrieval provider
- _[additional future areas to be noted by the team]_

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-15 | Initial scaffold created |
