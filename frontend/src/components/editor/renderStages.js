// Canonical render stage taxonomy + display mapping.
// Kept in one place so RenderPanel + RenderProgressView never drift.
//
// Each stage has:
//   • `range` — the [start, end] fraction of overall progress it covers,
//     used to draw the per-stage micro-bar.
//   • `eyebrow` — short, mono uppercase label.
//   • `title` — restrained serif-friendly label.
//   • `whisper` — single contemplative sentence shown while active.

export const STAGES = [
    {
        key: "queued",
        range: [0.0, 0.02],
        eyebrow: "Queued",
        title: "Awaiting the kiln",
        whisper: "The film waits its turn. Slow cinema is patient cinema.",
    },
    {
        key: "downloading_inputs",
        range: [0.02, 0.12],
        eyebrow: "Gathering",
        title: "Drawing media from the archive",
        whisper: "Each clip is being recalled from the vault, one at a time.",
    },
    {
        key: "preparing",
        range: [0.12, 0.15],
        eyebrow: "Preparing",
        title: "Setting the workshop",
        whisper: "Probing duration, dimensions, and the grain of each source.",
    },
    {
        key: "composing",
        range: [0.15, 0.45],
        eyebrow: "Composing",
        title: "Composing the timeline",
        whisper: "Resizing, letterboxing, and applying the muted palette per segment.",
    },
    {
        key: "audio_mixing",
        range: [0.45, 0.55],
        eyebrow: "Sound",
        title: "Weaving narration and ambience",
        whisper: "Lowering the room tone beneath the voice. Fading the edges.",
    },
    {
        key: "encoding",
        range: [0.55, 0.88],
        eyebrow: "Encoding",
        title: "Encoding the film",
        whisper: "Writing frames to disk. The longest, quietest stretch.",
    },
    {
        key: "encoding_complete",
        range: [0.88, 0.90],
        eyebrow: "Encoded",
        title: "Encoding complete",
        whisper: "The master file is written. Sealing it next.",
    },
    {
        key: "uploading",
        range: [0.90, 0.97],
        eyebrow: "Sending",
        title: "Sending to the vault",
        whisper: "Uploading the rendered film to long-term storage.",
    },
    {
        key: "finalizing",
        range: [0.97, 1.0],
        eyebrow: "Sealing",
        title: "Sealing the provenance",
        whisper: "Recording every cited clip alongside the rubric.",
    },
    {
        key: "completed",
        range: [1.0, 1.0],
        eyebrow: "Complete",
        title: "The film is ready",
        whisper: "Take a breath before watching it back.",
    },
    {
        key: "failed",
        range: [0.0, 1.0],
        eyebrow: "Interrupted",
        title: "The render did not complete",
        whisper: "Something resisted. Read the note below, then try once more.",
    },
];

// Stages shown in the vertical "phases" rail (excludes terminal/duplicate).
export const VISIBLE_STAGES = STAGES.filter((s) =>
    !["encoding_complete", "completed", "failed"].includes(s.key),
);

export const ACTIVE_STATUSES = new Set(["queued", "rendering"]);
export const TERMINAL_STATUSES = new Set(["completed", "failed"]);

export function stageMeta(key) {
    return STAGES.find((s) => s.key === key) || STAGES[0];
}

// Given a stage key + current overall progress, returns where the active
// stage sits in the rail (0..n-1) and a 0..1 sub-progress within that stage.
export function stagePosition(stageKey, progress) {
    const idx = VISIBLE_STAGES.findIndex((s) => s.key === stageKey);
    if (idx < 0) return { index: 0, sub: 0 };
    const s = VISIBLE_STAGES[idx];
    const span = Math.max(0.0001, s.range[1] - s.range[0]);
    const sub = Math.max(0, Math.min(1, (progress - s.range[0]) / span));
    return { index: idx, sub };
}

export function formatBytes(n) {
    if (n === null || n === undefined) return "—";
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
    return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function formatDuration(seconds) {
    if (!seconds || seconds < 0) return "—";
    const s = Math.floor(seconds);
    const m = Math.floor(s / 60);
    const rem = s % 60;
    if (m === 0) return `${rem}s`;
    return `${m}m ${String(rem).padStart(2, "0")}s`;
}
