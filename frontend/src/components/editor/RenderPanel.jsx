import React, { useMemo, useState } from "react";
import { fileUrl, fullUrl, endpoints } from "../../lib/api";
import useRenderJob from "../../hooks/useRenderJob";
import RenderProgressView from "./RenderProgressView";
import {
    stageMeta,
    formatDuration,
    formatBytes,
    ACTIVE_STATUSES,
} from "./renderStages";

const Field = ({ label, children }) => (
    <div>
        <label className="label-eyebrow block mb-2">{label}</label>
        {children}
    </div>
);

const PRESETS = [
    { label: "1080p · 24fps", width: 1920, height: 1080, fps: 24 },
    { label: "1080p · 30fps", width: 1920, height: 1080, fps: 30 },
    { label: "4K UHD · 24fps", width: 3840, height: 2160, fps: 24 },
    { label: "Square 1080 · 24fps", width: 1080, height: 1080, fps: 24 },
    { label: "Preview 640 · 24fps", width: 640, height: 360, fps: 24 },
];

export default function RenderPanel({ project, assets, onRenderComplete, onChange }) {
    const r = project.render_config || {};
    const set = (patch) => onChange({ ...project, render_config: { ...r, ...patch } });

    const [expanded, setExpanded] = useState(false);

    const {
        job, history, start, elapsedMs, etaMs, online,
    } = useRenderJob({
        projectId: project.id,
        onComplete: async () => {
            onRenderComplete?.();
        },
    });

    const completedRenders = useMemo(
        () => history.filter((h) => h.status === "completed"),
        [history],
    );
    const renderedAssets = useMemo(
        () => assets.filter((a) => a.kind === "render"),
        [assets],
    );
    const assetById = useMemo(
        () => Object.fromEntries(renderedAssets.map((a) => [a.id, a])),
        [renderedAssets],
    );

    const isActive = job && ACTIVE_STATUSES.has(job.status);
    const meta = job ? stageMeta(job.stage) : null;

    return (
        <div className="space-y-6" data-testid="render-panel">
            <Field label="Preset">
                <div className="grid grid-cols-2 gap-2">
                    {PRESETS.map((p) => {
                        const active = p.width === r.width && p.height === r.height && p.fps === r.fps;
                        return (
                            <button
                                key={p.label}
                                data-testid={`render-preset-${p.width}x${p.height}-${p.fps}`}
                                onClick={() => set({ width: p.width, height: p.height, fps: p.fps })}
                                className={`p-3 text-xs text-left border hairline transition-colors duration-500 ${
                                    active
                                        ? "border-ink bg-paper-200 text-ink"
                                        : "border-[rgba(26,25,24,0.12)] text-ink-faded hover:border-ink/40"
                                }`}
                            >
                                {p.label}
                            </button>
                        );
                    })}
                </div>
            </Field>

            <div className="grid grid-cols-2 gap-4">
                <Field label="Width">
                    <input
                        data-testid="render-width"
                        type="number" min="320" max="3840" step="2"
                        value={r.width ?? 1920}
                        onChange={(e) => set({ width: parseInt(e.target.value) || 1920 })}
                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2"
                    />
                </Field>
                <Field label="Height">
                    <input
                        data-testid="render-height"
                        type="number" min="240" max="2160" step="2"
                        value={r.height ?? 1080}
                        onChange={(e) => set({ height: parseInt(e.target.value) || 1080 })}
                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2"
                    />
                </Field>
                <Field label="FPS">
                    <input
                        data-testid="render-fps"
                        type="number" min="12" max="60" step="1"
                        value={r.fps ?? 24}
                        onChange={(e) => set({ fps: parseInt(e.target.value) || 24 })}
                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2"
                    />
                </Field>
                <Field label="Video bitrate">
                    <input
                        data-testid="render-bitrate"
                        value={r.video_bitrate ?? "6000k"}
                        onChange={(e) => set({ video_bitrate: e.target.value })}
                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2"
                    />
                </Field>
            </div>

            <button
                data-testid="start-render-btn"
                onClick={async () => {
                    const j = await start();
                    if (j) setExpanded(true);
                }}
                disabled={!project.segments?.length || isActive}
                className="w-full px-5 py-3 bg-ink text-paper text-sm tracking-wider hover:bg-ink-faded transition-colors duration-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {isActive ? "Rendering — let the film breathe…" : "Render the film →"}
            </button>

            {/* Inline summary — appears whenever there is a job (active or terminal) */}
            {job && (
                <div
                    data-testid="render-status"
                    className="border hairline border-[rgba(26,25,24,0.15)] p-4 space-y-3 bg-paper-50"
                >
                    <div className="flex items-baseline justify-between gap-3">
                        <div className="min-w-0">
                            <p className="label-eyebrow" data-testid="render-inline-eyebrow">
                                {meta?.eyebrow || job.status}
                            </p>
                            <p
                                className="text-sm font-serif text-ink mt-1 truncate"
                                style={{ fontFamily: "'Cormorant Garamond', Georgia, serif" }}
                                data-testid="render-inline-title"
                            >
                                {meta?.title || "—"}
                            </p>
                        </div>
                        <span
                            className="text-xs font-mono text-ink-muted whitespace-nowrap"
                            data-testid="render-inline-percent"
                        >
                            {Math.round((job.progress || 0) * 100)}%
                        </span>
                    </div>

                    <div className="h-px bg-[rgba(26,25,24,0.12)] overflow-hidden">
                        <div
                            data-testid="render-progress"
                            className={`h-full transition-all duration-700 ${
                                job.status === "failed" ? "bg-destructive" : "bg-ink"
                            }`}
                            style={{ width: `${Math.round((job.progress || 0) * 100)}%` }}
                        />
                    </div>

                    <div className="flex items-center justify-between text-[11px] font-mono text-ink-muted">
                        <span data-testid="render-inline-elapsed">
                            {formatDuration(elapsedMs / 1000)} elapsed
                            {etaMs ? ` · ≈ ${formatDuration(etaMs / 1000)} remaining` : ""}
                            {job.output_size_bytes
                                ? ` · ${formatBytes(job.output_size_bytes)}`
                                : ""}
                        </span>
                        {isActive && !online && (
                            <span
                                className="italic text-destructive"
                                data-testid="render-inline-offline"
                            >
                                offline
                            </span>
                        )}
                    </div>

                    {job.error && (
                        <p className="text-xs text-destructive italic" data-testid="render-inline-error">
                            {job.error}
                        </p>
                    )}

                    <div className="flex justify-end pt-1">
                        <button
                            data-testid="render-expand-btn"
                            onClick={() => setExpanded(true)}
                            className="text-[11px] font-mono tracking-widest uppercase text-ink-faded quiet-link"
                        >
                            Open full view ↗
                        </button>
                    </div>
                </div>
            )}

            {completedRenders.length > 0 && (
                <div className="pt-4 border-t hairline border-t-[rgba(26,25,24,0.1)]">
                    <p className="label-eyebrow mb-3">Past renders</p>
                    <ul className="space-y-3">
                        {completedRenders.slice(0, 4).map((h) => {
                            const a = assetById[h.output_asset_id];
                            if (!a) return null;
                            return (
                                <li key={h.id} data-testid={`past-render-${h.id}`} className="space-y-2">
                                    <video
                                        src={fileUrl(a.storage_path)}
                                        controls
                                        className="w-full bg-black"
                                        data-testid={`render-video-${h.id}`}
                                    />
                                    <div className="flex justify-between text-[11px] font-mono text-ink-muted">
                                        <span>
                                            {new Date(h.completed_at).toLocaleString(undefined, {
                                                month: "short", day: "numeric",
                                                hour: "2-digit", minute: "2-digit",
                                            })}
                                        </span>
                                        <div className="flex items-center gap-4">
                                            {h.provenance && (
                                                <a
                                                    href={fullUrl(endpoints.renderProvenance(h.id)) + "?format=text&download=1"}
                                                    data-testid={`provenance-${h.id}`}
                                                    className="quiet-link text-ink-faded"
                                                >
                                                    Provenance
                                                </a>
                                            )}
                                            <a
                                                href={fileUrl(a.storage_path)}
                                                download={a.original_filename}
                                                data-testid={`download-render-${h.id}`}
                                                className="quiet-link text-ink-faded"
                                            >
                                                Download
                                            </a>
                                        </div>
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            )}

            {expanded && job && (
                <RenderProgressView
                    job={job}
                    elapsedMs={elapsedMs}
                    etaMs={etaMs}
                    online={online}
                    onClose={() => setExpanded(false)}
                    onViewResult={() => setExpanded(false)}
                />
            )}
        </div>
    );
}
