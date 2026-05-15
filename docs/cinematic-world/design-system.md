# Design System

**Status:** `[SCAFFOLD]`

> This document is the canonical reference for the visual and interaction language
> of Tattvashila Cinematic World. It covers typography, colour, motion, component
> patterns, and the values that constrain all of the above.
> Implementation lives in `frontend/tailwind.config.js` and `frontend/src/index.css`.

---

## 1. Design Values

<!-- PLACEHOLDER
     Authors: State the 3–5 design values that constrain all visual decisions.
     These must be specific enough to resolve real design disagreements.
     Known from existing work: restraint, contemplation, breath.
     Do not list values you cannot defend with a concrete example.
-->

_To be authored by the founding team._

---

## 2. Colour

### 2.1 Palette

<!-- PLACEHOLDER
     Authors: Document the canonical colour palette with exact hex values.
     Known from PRD: paper-cream palette, soft warm highlights.
     Fill in the actual values from index.css / tailwind.config.js.
-->

| Token | Name | Hex | Usage |
|-------|------|-----|-------|
| `--color-paper` | Paper cream | _[hex]_ | Primary background |
| `--color-ink` | Ink | _[hex]_ | Primary text |
| `--color-warm-highlight` | Warm highlight | _[hex]_ | Accent, active states |
| _[additional tokens]_ | — | — | — |

### 2.2 Colour Constraints

<!-- PLACEHOLDER
     Authors: What colours may not be used? What contrast ratios are required?
     Are there colours that are prohibited because they conflict with the
     contemplative palette? (E.g., saturated primaries, neon accents.)
-->

_To be authored by the founding team._

### 2.3 Dark Mode

<!-- PLACEHOLDER
     Authors: Is a dark mode planned? What would "contemplative dark mode" mean —
     it is not simply inverted. If not planned, document the rationale.
-->

_To be authored by the founding team._

---

## 3. Typography

### 3.1 Typefaces

| Role | Typeface | Weights used | Notes |
|------|----------|-------------|-------|
| Display / headings | Cormorant Garamond | _[to be specified]_ | Serif, contemplative |
| Body / UI | IBM Plex Sans | _[to be specified]_ | Neutral, legible |

### 3.2 Type Scale

<!-- PLACEHOLDER
     Authors: Document the type scale in use.
     Are these Tailwind defaults or custom? What is the base size?
     What tracking/leading values apply to each level?
-->

| Level | Tailwind class | Size | Use case |
|-------|---------------|------|---------|
| _[to be defined]_ | — | — | — |

### 3.3 Typography Rules

<!-- PLACEHOLDER
     Authors: What typographic rules apply throughout the UI?
     Consider: maximum line length, minimum body size on mobile, use of italics,
     use of all-caps, letter-spacing conventions.
-->

_To be authored by the founding team._

---

## 4. Motion

### 4.1 Motion Principle

<!-- PLACEHOLDER
     Authors: The PRD specifies "slow opacity-only motion". Document what this means:
     - Which elements animate?
     - What duration range is acceptable?
     - What easing functions are used?
     - What triggers animation?
-->

Known constraint: **opacity transitions only**. No translate, scale, or rotate animations
in the UI layer. Duration and easing to be specified.

_Specifics to be authored by the founding team._

### 4.2 Reduced Motion

<!-- PLACEHOLDER
     Authors: How does the system respond to `prefers-reduced-motion`?
     Are opacity transitions themselves disabled, or only supplementary animations?
-->

_To be authored by the founding team._

### 4.3 Prohibited Motion Patterns

<!-- PLACEHOLDER
     Authors: List animation patterns that are explicitly prohibited.
     Consider: spring physics, bounce easing, parallax, attention-seeking
     micro-interactions, loading spinners that suggest urgency.
-->

_To be authored by the founding team._

---

## 5. Component Patterns

### 5.1 Component Library

The frontend uses **Shadcn UI** primitives over Tailwind CSS.
Components are in `frontend/src/components/ui/`.

<!-- PLACEHOLDER
     Authors: Document which Shadcn components are used and any customisations
     applied. Note any components that are prohibited (too visually active for
     the contemplative aesthetic).
-->

_Component inventory to be authored by the founding team._

### 5.2 Custom Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `Timeline` | `frontend/src/components/editor/Timeline.jsx` | Segment sequence editor |
| `MediaLibrary` | `frontend/src/components/editor/MediaLibrary.jsx` | Asset browser |
| `RenderPanel` | `frontend/src/components/editor/RenderPanel.jsx` | Render configuration and launch |
| `GradingPanel` | `frontend/src/components/editor/GradingPanel.jsx` | Visual grading controls |
| `NarrationPanel` | `frontend/src/components/editor/NarrationPanel.jsx` | TTS and narration upload |
| `AmbiencePanel` | `frontend/src/components/editor/AmbiencePanel.jsx` | Ambient audio selection |
| `RetrievalDialog` | `frontend/src/components/editor/RetrievalDialog.jsx` | AI-guided clip retrieval |
| `RenderProgressView` | `frontend/src/components/editor/RenderProgressView.jsx` | Render stage display |

<!-- PLACEHOLDER
     Authors: For each component, document: what design values it embodies,
     any constraints on modification, and any known design debt.
-->

### 5.3 Spacing System

<!-- PLACEHOLDER
     Authors: Document the spacing scale. Are these Tailwind defaults?
     Is there a minimum spacing between interactive elements?
     What padding/margin conventions apply to the editor layout?
-->

_To be authored by the founding team._

---

## 6. Layout Architecture

<!-- PLACEHOLDER
     Authors: Document the macro layout structure:
     - The Editor page (header, sidebar, main area, panels)
     - The Projects catalogue
     - The Landing / onboarding flow
     How do these adapt to mobile viewports? See mobile-first-ux.md for detail.
-->

_To be authored by the founding team._

---

## 7. Iconography

<!-- PLACEHOLDER
     Authors: What icon set is used? What is the style guidance (line weight,
     fill vs. outline, size conventions)? Are custom icons required?
-->

_To be authored by the founding team._

---

## 8. Design Debt and Known Issues

<!-- Maintain this section honestly. Remove entries when resolved. -->

| Issue | Location | Priority | Notes |
|-------|----------|----------|-------|
| _[to be recorded as found]_ | — | — | — |

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-15 | Initial scaffold created |
