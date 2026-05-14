# Tattvashila — Product Requirements (Living Document)

## Original Problem Statement
A contemplative cinematic editing and atmospheric media system. NOT a social-media
video generator. The films should feel calm, observational, grounded, emotionally
mature, visually restrained. The system must never optimize for stimulation.
Grounded in *dharma*. Carried with integrity.

## Architecture
- **Backend**: FastAPI + MongoDB. Reusable Python `pipeline/` module (MoviePy + FFmpeg)
  also runnable as `python -m pipeline render <config.json>`.
- **Frontend**: React (CRA + Tailwind + Shadcn primitives). Restrained typography
  (Cormorant Garamond + IBM Plex Sans), paper-cream palette, slow opacity-only motion.
- **Storage**: Emergent Object Storage for all media (clips, narration, ambient,
  renders). MongoDB stores metadata only.
- **Integrations**: OpenAI Text-to-Speech via Emergent universal LLM key.

## User Personas
1. **The cultural editor** — assembling a slow-cinema piece for an institutional
   archive or foundation channel; wants restraint, not virality.
2. **The independent essayist** — recording a measured voiceover, draping it over
   footage with breath between thoughts.
3. **The atelier** — using the Python pipeline programmatically across many films
   that share grading and pacing.

## Core Requirements (static)
- Restrained transitions only: fade / dissolve / crossfade / hard cut.
- Black-frame pauses as first-class segments.
- Two narration sources: uploaded audio file OR OpenAI TTS.
- Curated built-in ambient library (room_tone, wind, rain, forest, drone, paper)
  PLUS user uploads.
- Optional muted palette, soft warm highlights, low contrast, subtle film grain.
- Configurable render per work (resolution, fps, bitrate).
- Reusable as a Python library / CLI.

## What's Been Implemented — 2026-02 (v0.1)
- ✅ Object Storage helpers (`storage.py`) with retry on key expiry
- ✅ OpenAI TTS service (`narration.py`) — 6 contemplative voices, 2 models
- ✅ Built-in ambient library (`ambient_library.py`) — 6 FFmpeg-synthesised presets
- ✅ Cinematic `pipeline/` module: `transitions`, `grading`, `renderer`, CLI
- ✅ Pydantic models for `MediaAsset`, `Project`, `Segment`, `RenderJob`
- ✅ FastAPI routes: projects CRUD, media upload+list+delete, TTS, ambient library,
  file serving, render start + status + history
- ✅ MoviePy + Pillow-10 ANTIALIAS shim
- ✅ Frontend pages: Landing (foundations), Projects (catalogue), Editor (workshop)
- ✅ Editor: media library (3 tabs), timeline with drag-free segment list, right-panel
  tabs (narration / ambience / grading / render), auto-save 1.5s after edits
- ✅ Render preset buttons (1080p24/30, 4K24, Square 1080, Preview 640)
- ✅ Past renders show inline with download links — refreshed automatically on completion
- ✅ E2E tested: clip upload → timeline assembly → TTS narration → built-in ambient →
  render → MP4 download via object storage

## What's Been Implemented — 2026-02 (v0.2 — Atmospheric Retrieval)
- ✅ `retrieval/scene_analyzer.py` — Claude Sonnet 4.5 produces a structured
  cinematic rubric (tone, pacing, environment, atmosphere, restraint_level,
  search_queries, preferred/rejected keywords, rationale)
- ✅ `retrieval/providers.py` — concurrent Pexels Videos + Pixabay Videos search;
  local archive placeholder
- ✅ `retrieval/ranker.py` — batched Claude ranking 0–1 with one-line rationale,
  heuristic pre-filter on rejected_keywords, hard threshold 0.55 in Contemplative Mode
- ✅ `retrieval/trim.py` — adaptive 4–12s trim window, narration-aware, falls back
  to a deterministic centred window
- ✅ Routes: `POST /api/retrieval/analyze`, `/search`, `/assemble`
- ✅ `MediaAsset` now carries `provider` / `provider_external_id` / `source_url` /
  `author` attribution
- ✅ Frontend `RetrievalDialog.jsx` modal — scene textarea + 4 example chips,
  Contemplative Mode toggle, narration-sync toggle, analyse button → rubric card +
  search query chips → ranked clip grid (thumbnail, hover-preview video, score badge,
  rationale italic, tags, author) → "Import & assemble" downloads, trims, and
  appends segments to the timeline with restrained transitions
- ✅ Manual upload workflow preserved; retrieval is purely additive
- ✅ E2E tested (iteration 2): 13/13 backend tests + frontend Playwright pass

## What's Been Implemented — 2026-02 (v0.3 — Stabilisation & Production Hardening)
- ✅ Backend architecture split into a `services/` layer:
  - `services/render_service.py` — `load_render_inputs`, `upload_render_output`,
    `find_active_render`, `cleanup_paths`
  - `services/retrieval_service.py` — `download_url_bytes` (retried),
    `import_stock_clip`, `build_retrieval_segment`
- ✅ `utils/retry.py` — `retry_async` with exponential backoff; retries on
  429/5xx and connection errors only
- ✅ `utils/cache.py` — `TTLCache` (300s ttl); search endpoint now returns
  cached responses in ~14 ms vs ~25 s uncached (1800× speedup)
- ✅ `retrieval/providers.py` — extracted `_parse_pexels_video` /
  `_parse_pixabay_hit`; HTTP calls wrapped in retries; partial-provider failure
  no longer fails the whole search
- ✅ `retrieval/ranker.py` — split into `_pre_filter` (now also drops zero-dim
  clips) / `_build_payload` / `_call_ranker_llm` / `_apply_scores` /
  `_filter_threshold`
- ✅ Render-queue safety — duplicate POST `/api/projects/{id}/render` while
  a job is queued/rendering returns the existing job (no double-render)
- ✅ Attribution persistence — every retrieval-imported MediaAsset stores
  `provider`, `provider_external_id`, `source_url`, `author` in MongoDB
- ✅ Frontend `ErrorBoundary` at root, `lib/log.js` production-gated logger
  with `niceMessage(err)` helper; every `console.error` replaced
- ✅ Component refactor:
  - `hooks/useEditorState.js` — owns project/assets/save/dirty + debounced autosave
  - `hooks/useRetrieval.js` — state machine: idle/analyzing/searched/assembling
  - `hooks/useRenderJob.js` — polling + history; ref-based onComplete to avoid
    stale closures
  - `RetrievalRubric.jsx`, `RetrievalClipCard.jsx` (memoised), `EditorHeader.jsx`
    (a11y aria labels), `EditorPreview.jsx` — small, focused subcomponents
  - `Editor.jsx` 333 → 186 lines · `RetrievalDialog.jsx` 442 → 239 lines ·
    `RenderPanel.jsx` 243 → 188 lines · `server.py` 733 → ~600 lines
- ✅ Mobile responsiveness — Editor 3-col stacks vertically <lg; RetrievalDialog
  single-column clip grid <sm; header "Atmospheric retrieval" → "Retrieve" <sm;
  verified no horizontal scroll at 414×900
- ✅ E2E tested (iteration 3): 11/11 new stabilisation tests + full regression
  (29/30 across all suites; the single non-regression failure was upstream
  Pixabay returning a zero-dim clip — now fixed by the pre-filter)

## What's Been Implemented — 2026-05 (v0.5 — Render Progress Experience)
- ✅ **Backend granular stage taxonomy**: `_run_render` in `server.py` and
  `pipeline/renderer.py` now publish a precise sequence of stages:
  `queued → downloading_inputs → preparing → composing → audio_mixing →
  encoding → uploading → finalizing → completed`. The progress fraction
  is monotonic 0.0 → 1.0.
- ✅ Two new render_jobs columns (Alembic revision `a1b2c3d4e5f6`):
  - `queue_position` — integer, computed at insert as the current count of
    queued+rendering jobs (so the very first one in a quiet queue reports
    0 = "next up").
  - `output_size_bytes` — populated when the MP4 lands on disk and again
    when uploaded, so the inline summary and overlay can show "22.0 MB"
    without waiting on /media metadata.
- ✅ `services/render_service.load_render_inputs` now accepts a
  `progress_cb(done, total)` so `_run_render` can stream sub-progress
  during the download phase.
- ✅ `storage.py` rewritten with `_do_request` retry wrapper —
  exponential backoff on 403 + 5xx + connection errors (3 attempts),
  with automatic storage-key re-initialisation on each retry. Renders no
  longer crash mid-upload on transient Emergent storage hiccups.
- ✅ **Frontend institutional overlay** — `RenderProgressView.jsx`:
  full-screen ivory/charcoal contemplative layout with vertical phase
  rail (past/active/pending dots), per-phase title + whisper sentence,
  master linear progress bar, elapsed/ETA/master-file-size/queue meta,
  network-status indicator (online/offline), Escape-to-close.
- ✅ Inline render summary in `RenderPanel.jsx` shows the same data in
  miniature with an "Open full view ↗" link that mounts the overlay.
- ✅ `hooks/useRenderJob.js` extended: elapsed-time computation from
  `started_at`, naive ETA from progress-vs-elapsed, online/offline
  tracking via window events, 2s poll cadence.
- ✅ Stage taxonomy + display copy lives in
  `components/editor/renderStages.js` so RenderPanel and
  RenderProgressView never drift.
- ✅ E2E tested (iteration 4): 8/8 backend pytest in
  `/app/backend/tests/test_render_progress.py` + full Playwright frontend
  flow (start → overlay opens → phase rail asserts → terminal state →
  Past renders increments) — 100% pass rate. No bugs.


### P0 (blocking)
- (none — MVP is functional)

### P1 (next phase)
- Drag-and-drop reordering of timeline segments (currently up/down buttons)
- In-browser ffmpeg.wasm scrub preview of full timeline (not just first frame)
- Per-segment colour grading overrides (currently project-level only)
- Streaming uploads for large clips (currently buffered fully in memory, 500MB cap)
- Render queue with concurrent renders & priority

### P2 (later)
- Project templates ("Quiet Essay", "Archival Profile", "Foundation Address")
- Shareable, signed read-only view URL of a completed film
- Subtitle/caption track support
- Multi-language narration (Hindi, Sanskrit transliteration)
- Audio ducking — auto-attenuate ambient when narration plays

## Known Limitations
- TTS limited to 4096 chars per call (OpenAI constraint). Split long scripts client-side.
- Renders run in-process via FastAPI BackgroundTasks — fine for single-tenant MVP,
  not for production scale (use Celery / RQ for multi-tenant).
- Preview area only shows the first clip's static frame, not the assembled film.

## Files of Interest
- `/app/backend/server.py` — API
- `/app/backend/pipeline/` — reusable engine
- `/app/frontend/src/pages/Editor.jsx` — workshop UI
- `/app/design_guidelines.json` — visual language
