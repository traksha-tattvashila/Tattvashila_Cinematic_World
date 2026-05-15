# Tattvashila Cinematic World — Documentation

This directory is the **source of truth** for all architectural, philosophical, and
product decisions related to **Tattvashila Cinematic World** — the cinematic media
infrastructure, filmmaking system, and contemplative archive platform.

---

## Scope

These docs cover:

- Cinematic and media infrastructure
- Filmmaking and retrieval systems
- Archive architecture and philosophy
- Narrative and editorial workflows
- Media ethics and truth-first principles
- Mobile-first cinematic UX
- Design system and visual language
- Technical architecture decisions

These docs do **not** cover:

- Traksha infrastructure or governance
- Tattvashila ecosystem-wide philosophy (only what directly informs cinematic tools)
- Unrelated product lines

---

## Document Hierarchy

```
docs/
├── README.md                          ← You are here. Start here.
│
├── tattvashila/
│   ├── philosophy.md                  ← Parent ecosystem: what informs this work
│   └── principles.md                  ← Operating principles inherited by Cinematic World
│
└── cinematic-world/
    ├── source-of-truth.md             ← PRIMARY REFERENCE. Read this first.
    ├── architecture.md                ← System architecture and technical decisions
    ├── cinematic-philosophy.md        ← What this tool believes about cinema
    ├── media-ethics.md                ← How media is sourced, used, attributed
    ├── archive-philosophy.md          ← How films are stored, versioned, preserved
    ├── retrieval-principles.md        ← How clips are found, ranked, and selected
    ├── mobile-first-ux.md             ← Mobile UX design principles and constraints
    ├── design-system.md               ← Visual language, typography, motion, palette
    └── decision-log.md                ← Chronological record of architectural decisions
```

---

## How to Use These Docs

### For humans (developers, editors, contributors)

1. Read `cinematic-world/source-of-truth.md` before making any product, UI, or
   architectural decision.
2. Check `decision-log.md` to understand why things are the way they are.
3. Update `decision-log.md` when you make a significant decision.
4. Keep philosophy docs minimal and honest — do not add entries you cannot stand behind.

### For AI agents

> **Mandatory read before any architectural, product, or UI change:**
> `docs/cinematic-world/source-of-truth.md`

Rules for AI agents working in this repository:

- Read `source-of-truth.md` in full before proposing structural changes.
- Do not introduce terminology inconsistent with the vocabulary established in these docs.
- Do not optimise for engagement, virality, or stimulation — this is an anti-goal
  documented in `source-of-truth.md`.
- Preserve the contemplative UX philosophy in all frontend work.
- When in doubt, choose restraint over feature addition.
- Log significant decisions to `decision-log.md`.
- Do not overwrite placeholder sections with invented content — leave them for human authors.

---

## Document Status Legend

Documents may carry a status marker in their header:

| Status | Meaning |
|--------|---------|
| `[SCAFFOLD]` | Structure only. Awaiting human-authored content. |
| `[DRAFT]` | Partially authored. Not yet canonical. |
| `[STABLE]` | Reviewed and considered canonical. Change with care. |
| `[DEPRECATED]` | Superseded. Kept for historical reference only. |

---

## Maintenance

- Keep files minimal. Prefer short, precise statements over long prose.
- One decision per entry in `decision-log.md`.
- Prefer updating existing sections over creating new files.
- New top-level files require a corresponding entry in this README.
