# Archive Philosophy

**Status:** `[SCAFFOLD]`

> This document defines how Tattvashila Cinematic World thinks about the
> preservation, versioning, and long-term stewardship of films and their
> associated data. An archive is not a dump — it is a considered act.

---

## 1. What an Archive Is (For This System)

<!-- PLACEHOLDER
     Authors: Define what "archive" means in this context. Is it about:
     - Institutional preservation?
     - Personal film history?
     - Provenance documentation?
     - Access over time?
     Be specific about what the system currently stores and what it aspires to.
-->

_To be authored by the founding team._

---

## 2. What Is Archived

### 2.1 Current Archivable Artefacts

| Artefact | Where stored | Format | Retention |
|----------|-------------|--------|-----------|
| Rendered film (MP4) | Emergent Object Storage | MP4, H.264 | _[to be defined]_ |
| Render provenance (JSON) | Emergent Object Storage | JSON | _[to be defined]_ |
| Project metadata | Supabase Postgres | DB rows | _[to be defined]_ |
| Media assets (clips, audio) | Emergent Object Storage | Various | _[to be defined]_ |
| Narration audio | Emergent Object Storage | MP3 | _[to be defined]_ |

### 2.2 What Is Not Archived

<!-- PLACEHOLDER
     Authors: Explicitly list what is intentionally ephemeral —
     what is discarded after use, and why.
-->

_To be authored by the founding team._

---

## 3. Preservation Principles

<!-- PLACEHOLDER
     Authors: What obligations does the system have to works it has produced?
     Consider:
     - Can a film be deleted by the user? By the system?
     - What happens to a film if a provider (Emergent, Supabase) shuts down?
     - Is there a concept of a "master" vs "distribution" copy?
     - Is bit-rot prevention in scope?
-->

_To be authored by the founding team._

---

## 4. Versioning

<!-- PLACEHOLDER
     Authors: Films are re-renderable from project data. What is the policy on:
     - Storing multiple renders of the same project?
     - Tracking changes to a project over time?
     - What constitutes a "version" vs. a "render"?
     Current system: render history is stored per project (see `/projects/{id}/renders`).
-->

_To be authored by the founding team._

---

## 5. Provenance as Archive

The system generates a provenance record for every completed render. This record includes:

- `citations` — source attribution for each clip used
- `rubric` — the cinematic rubric used to guide retrieval
- `segments` — the full timeline with timecodes and clip IDs
- `retrieved_at` / `rendered_at` — temporal record

<!-- PLACEHOLDER
     Authors: How should provenance records be treated archivally?
     Are they attached to the film itself (embedded metadata)?
     Are they discoverable by viewers? By institutions?
     What is their longevity relative to the film?
-->

_Provenance as archive to be authored by the founding team._

---

## 6. Access and Shareability

<!-- PLACEHOLDER
     Authors: What access modes does the archive support?
     Known from PRD: "Shareable, signed read-only view URL of a completed film."
     What is the policy on public vs. private archives?
     Can films be shared with institutions? With the public?
     Is there an embargo period?
-->

_To be authored by the founding team._

---

## 7. Deletion and the Right to Be Forgotten

<!-- PLACEHOLDER
     Authors: What happens when a user deletes a project or a film?
     Are media assets purged from object storage immediately?
     Is there a grace period? A soft-delete?
     How does this interact with provenance records?
-->

_To be authored by the founding team._

---

## 8. Long-Term Infrastructure Considerations

<!-- PLACEHOLDER
     Authors: The archive depends on third-party infrastructure (Emergent Object
     Storage, Supabase). What is the contingency plan if these services change?
     Is there a vendor lock-in concern?
     What would a migration path look like?
-->

_To be authored by the founding team._

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-15 | Initial scaffold created |
