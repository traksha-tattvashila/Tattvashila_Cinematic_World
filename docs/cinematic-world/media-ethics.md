# Media Ethics

**Status:** `[SCAFFOLD]`

> This document defines the ethical framework governing how media is sourced,
> used, attributed, stored, and removed in Tattvashila Cinematic World.
> It covers stock footage, user-uploaded content, AI-generated media, narration,
> and ambient audio.

---

## 1. Guiding Ethical Framework

<!-- PLACEHOLDER
     Authors: State the ethical framework that governs media use in this system.
     What principles (from Tattvashila philosophy or independent of it) govern
     how media is acquired and treated? Be concrete and non-platitudinous.
-->

_To be authored by the founding team._

---

## 2. Stock Footage — Sourcing and Use

### 2.1 Current Providers

| Provider | API | License type | Current key status |
|----------|-----|-------------|-------------------|
| Pexels | Videos API | Pexels License | Active (rotate after history purge) |
| Pixabay | Videos API | Pixabay License | Active (rotate after history purge) |

### 2.2 Acceptable Use

<!-- PLACEHOLDER
     Authors: What are the permitted uses of Pexels and Pixabay content within
     films created by this system? Reference the actual license terms.
     Are commercial uses permitted? Attribution required?
-->

_To be authored with reference to actual license terms._

### 2.3 Provenance Tracking

The system records clip provenance in the render provenance JSON:

```
provenance.citations     — source attribution per clip
provenance.segments      — which clip appeared at which timecode
provenance.retrieved_at  — when retrieval occurred
```

<!-- PLACEHOLDER
     Authors: Document the provenance policy. Is provenance data exposed to
     end users? Is it embedded in the output file? Is it archived separately?
     What is the retention policy for provenance records?
-->

_Provenance policy to be authored by the founding team._

### 2.4 Prohibited Content

<!-- PLACEHOLDER
     Authors: Define what categories of stock footage must never be retrieved,
     assembled, or rendered — regardless of whether the provider serves it.
     Examples to consider (do not treat as final): misleading contexts,
     content that misrepresents subjects, content with licensing violations.
-->

_Prohibited content categories to be authored by the founding team._

---

## 3. User-Uploaded Media

### 3.1 What Users May Upload

<!-- PLACEHOLDER
     Authors: Define what media types and categories users are permitted to
     upload. What rights must users hold over uploaded content?
     What do users warrant by uploading?
-->

_To be authored by the founding team._

### 3.2 Storage and Retention

<!-- PLACEHOLDER
     Authors: Where is uploaded media stored? (Currently: Emergent Object Storage)
     How long is it retained? What happens on account deletion?
     Is media encrypted at rest?
-->

_Storage and retention policy to be authored by the founding team._

### 3.3 Removal and Rights Disputes

<!-- PLACEHOLDER
     Authors: How are takedown requests handled?
     How are rights disputes resolved?
     Who is the point of contact?
-->

_To be authored by the founding team._

---

## 4. AI-Generated Media

### 4.1 TTS Narration

The system generates narration audio via OpenAI TTS (routed through Emergent).
Generated audio is stored in Emergent Object Storage and associated with a render job.

<!-- PLACEHOLDER
     Authors: What is the disclosure policy for AI-generated narration?
     Must films disclose when narration is AI-generated?
     How is this labelled in provenance records?
-->

_Disclosure policy to be authored by the founding team._

### 4.2 AI-Assisted Retrieval

The system uses Claude Sonnet to analyse scenes and rank clips.
The AI does not generate any visual content — it selects from human-created footage.

<!-- PLACEHOLDER
     Authors: How should AI involvement in clip selection be disclosed?
     Is the ranking process considered editorial or algorithmic?
-->

_To be authored by the founding team._

### 4.3 Prohibited AI Uses

<!-- PLACEHOLDER
     Authors: Define what AI may not be used for in this system.
     Consider: deepfakes, synthetic subjects, misleading reconstruction, etc.
-->

_To be authored by the founding team._

---

## 5. Ambient Audio

Built-in ambient presets are synthesised by the system (not sourced from third parties).
User-uploaded ambient audio follows the same policy as user-uploaded media (Section 3).

---

## 6. Truth and Representation

<!-- PLACEHOLDER
     Authors: This is a "truth-first media system" — what does that mean
     operationally? What obligations does the system have to the accuracy
     of representation in assembled films?
     When does a film assembled from stock footage make an implicit truth claim?
     How should the system handle this?
-->

_To be authored by the founding team._

---

## 7. Revision and Review

This document should be reviewed when:

- A new media source or provider is added
- A new AI capability is introduced
- A rights dispute is resolved
- Applicable law changes

---

## Revision History

| Date | Change |
|------|--------|
| 2026-05-15 | Initial scaffold created |
