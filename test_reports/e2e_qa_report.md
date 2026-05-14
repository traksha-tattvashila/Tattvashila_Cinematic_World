# Tattvashila LOW-CREDIT E2E QA Report

**Date:** 2026-05-14 06:46:45 UTC

## Summary

- **Tests Passed:** 13/16
- **Bugs Found:** 2
- **Stability Issues:** 0
- **Render Issues:** 0
- **Deployment Risks:** 0

## Critical Path Results

- **✅ PASS** — GET /api/health
  - status=ok, presets=6, voices=6
- **✅ PASS** — GET /api/ambient/library
  - 6 presets available
- **✅ PASS** — GET /api/narration/voices
  - 6 voices, 2 models
- **✅ PASS** — POST /api/projects
  - project_id=dfb8de11-e85b-438a-be20-3e60b286962c
- **✅ PASS** — GET /api/projects/{id}
  - Project persisted correctly
- **✅ PASS** — POST /api/retrieval/analyze
  - Rubric generated in 5.7s
- **✅ PASS** — POST /api/retrieval/search
  - 12 clips retrieved in 18.1s
- **✅ PASS** — POST /api/retrieval/assemble
  - 2 segments imported in 7.8s
- **✅ PASS** — GET /api/media (attribution)
  - Asset 76de3979-4a09-44f6-8e8c-98926cfc76be: pexels/28829378
- **✅ PASS** — GET /api/media (attribution)
  - Asset 4276555b-12f5-4b6b-a7ce-a7684a086c52: pexels/10849309
- **❌ FAIL** — POST /api/narration/tts
  - HTTP 502: {"detail":"TTS failed: Failed to generate speech: Error code: 400 - {'error': {'message': 'Budget has been exceeded! Current cost: 1.0132439999999998, Max budget: 1.001', 'type': 'budget_exceeded', 'param': None, 'code': '400'}}"}
- **❌ FAIL** — PATCH /api/projects/{id}
  - Missing project_id or tts_asset_id
- **✅ PASS** — POST /api/projects/{id}/render
  - job_id=f8fb303b-c664-4a49-b011-e4b61aa79f7c
- **✅ PASS** — Render completion
  - Completed in 58.7s
- **❌ FAIL** — Render output reachable
  - HEAD https://repo-puller-29.preview.emergentagent.com/api/files/tattvashila/render/f1181398-a1d6-4e82-bca4-736b436ad2b0.mp4 → 405
- **✅ PASS** — GET /api/projects/{id}/renders
  - 1 render(s) listed, including job f8fb303b-c664-4a49-b011-e4b61aa79f7c

## Discovered Bugs

- POST /api/narration/tts returned 502
- Render output URL not reachable: https://repo-puller-29.preview.emergentagent.com/api/files/tattvashila/render/f1181398-a1d6-4e82-bca4-736b436ad2b0.mp4

## Stability Issues

None

## Render Issues

None

## Retrieval Quality Observations

- Rubric emotional_tone=quiet anticipation, pacing=glacial, restraint=0.92
- Search queries: ['misty river morning silence', 'fog water surface dawn', 'quiet riverbank first light', 'still water vapor sunrise']
- Clip 0: pexels/10849309 by Tom Fisk
- Clip 1: pexels/28829378 by Matthias Groeneveld
- Clip 2: pexels/32329775 by Tom Fisk

## Deployment Risks

None
