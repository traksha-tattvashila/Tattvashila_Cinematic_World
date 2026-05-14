import React, { useState } from "react";
import { Plus, X, ArrowUp, ArrowDown, GripVertical } from "lucide-react";

const TRANSITIONS = [
    { value: "none", label: "Cut" },
    { value: "fade", label: "Fade" },
    { value: "crossfade", label: "Crossfade" },
    { value: "dissolve", label: "Slow Dissolve" },
];

export default function Timeline({ project, assets, onChange }) {
    const segments = project.segments || [];
    const [dragIdx, setDragIdx] = useState(null);
    const [dropIdx, setDropIdx] = useState(null);

    const setSegments = (next) => onChange({ ...project, segments: next });

    const updateSeg = (idx, patch) => {
        const next = [...segments];
        next[idx] = { ...next[idx], ...patch };
        setSegments(next);
    };

    const removeSeg = (idx) => setSegments(segments.filter((_, i) => i !== idx));

    const move = (idx, dir) => {
        const j = idx + dir;
        if (j < 0 || j >= segments.length) return;
        const next = [...segments];
        [next[idx], next[j]] = [next[j], next[idx]];
        setSegments(next);
    };

    const reorder = (from, to) => {
        if (from === to || from == null || to == null) return;
        const next = [...segments];
        const [moved] = next.splice(from, 1);
        next.splice(to, 0, moved);
        setSegments(next);
    };

    const addPause = () => {
        setSegments([
            ...segments,
            {
                id: crypto.randomUUID(),
                kind: "pause",
                duration: 3,
                start_offset: 0,
                transition_in: "fade",
                transition_in_duration: 1.5,
            },
        ]);
    };

    const assetMap = Object.fromEntries(assets.map((a) => [a.id, a]));
    const totalDuration = segments.reduce((s, x) => s + (x.duration || 0), 0);

    return (
        <div className="border hairline border-[rgba(26,25,24,0.15)] bg-paper-50" data-testid="timeline">
            <div className="flex items-baseline justify-between border-b hairline border-b-[rgba(26,25,24,0.12)] px-6 py-4">
                <div className="flex items-baseline gap-6">
                    <p className="label-eyebrow">Timeline</p>
                    <p
                        className="text-xs font-mono text-ink-muted tracking-wider"
                        data-testid="timeline-total-duration"
                    >
                        TOTAL · {totalDuration.toFixed(1)}s · {segments.length} SEG
                    </p>
                </div>
                <button
                    data-testid="add-pause-btn"
                    onClick={addPause}
                    className="flex items-center gap-1.5 text-xs text-ink-faded quiet-link"
                >
                    <Plus size={13} strokeWidth={1.25} /> Add black pause
                </button>
            </div>

            {segments.length === 0 ? (
                <div className="p-12 text-center">
                    <p className="font-serif text-xl text-ink-faded italic mb-1">
                        The timeline is silent.
                    </p>
                    <p className="text-xs text-ink-muted">
                        Place a clip from the library, or insert a pause.
                    </p>
                </div>
            ) : (
                <ol className="divide-y hairline divide-[rgba(26,25,24,0.1)]">
                    {segments.map((seg, idx) => {
                        const asset = seg.asset_id ? assetMap[seg.asset_id] : null;
                        const isPause = seg.kind === "pause";
                        const isDragging = dragIdx === idx;
                        const isDropTarget = dropIdx === idx && dragIdx !== idx;
                        return (
                            <li
                                key={seg.id}
                                data-testid={`segment-${idx}`}
                                draggable
                                onDragStart={(e) => {
                                    setDragIdx(idx);
                                    e.dataTransfer.effectAllowed = "move";
                                    try { e.dataTransfer.setData("text/plain", String(idx)); } catch { /* ignore */ }
                                }}
                                onDragOver={(e) => {
                                    e.preventDefault();
                                    e.dataTransfer.dropEffect = "move";
                                    setDropIdx(idx);
                                }}
                                onDragLeave={() => {
                                    if (dropIdx === idx) setDropIdx(null);
                                }}
                                onDrop={(e) => {
                                    e.preventDefault();
                                    reorder(dragIdx, idx);
                                    setDragIdx(null);
                                    setDropIdx(null);
                                }}
                                onDragEnd={() => { setDragIdx(null); setDropIdx(null); }}
                                className={`grid grid-cols-12 gap-4 items-center px-6 py-5 transition-all duration-300 ${
                                    isDragging ? "opacity-40" : ""
                                } ${
                                    isDropTarget ? "bg-paper-200 border-l-2 border-l-ink" : "hover:bg-paper-200"
                                }`}
                            >
                                <span className="col-span-1 flex items-center gap-2 font-mono text-[11px] text-ink-muted tracking-widest">
                                    <span
                                        className="cursor-grab active:cursor-grabbing text-ink-soft hover:text-ink"
                                        data-testid={`drag-handle-${idx}`}
                                        aria-label="Drag to reorder"
                                    >
                                        <GripVertical size={13} strokeWidth={1.25} />
                                    </span>
                                    {String(idx + 1).padStart(2, "0")}
                                </span>
                                <div className="col-span-3">
                                    <p className={`text-sm ${isPause ? "italic text-ink-faded" : "text-ink"}`}>
                                        {isPause ? "Black pause" : asset?.original_filename || "—"}
                                    </p>
                                    <p className="text-[10px] font-mono text-ink-muted tracking-wider uppercase mt-0.5">
                                        {isPause ? "Pause" : "Clip"}
                                        {asset?.duration ? ` · src ${asset.duration.toFixed(1)}s` : ""}
                                        {asset?.provider ? ` · ${asset.provider}` : ""}
                                    </p>
                                </div>

                                <div className="col-span-2">
                                    <label className="text-[10px] text-ink-muted tracking-wider uppercase block mb-1">
                                        Duration
                                    </label>
                                    <input
                                        data-testid={`segment-duration-${idx}`}
                                        type="number"
                                        step="0.5"
                                        min="0.5"
                                        value={seg.duration}
                                        onChange={(e) =>
                                            updateSeg(idx, { duration: parseFloat(e.target.value) || 0.5 })
                                        }
                                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-1"
                                    />
                                </div>

                                {!isPause && (
                                    <div className="col-span-2">
                                        <label className="text-[10px] text-ink-muted tracking-wider uppercase block mb-1">
                                            Start offset
                                        </label>
                                        <input
                                            data-testid={`segment-offset-${idx}`}
                                            type="number"
                                            step="0.5"
                                            min="0"
                                            value={seg.start_offset}
                                            onChange={(e) =>
                                                updateSeg(idx, { start_offset: parseFloat(e.target.value) || 0 })
                                            }
                                            className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-1"
                                        />
                                    </div>
                                )}

                                <div className={isPause ? "col-span-4" : "col-span-2"}>
                                    <label className="text-[10px] text-ink-muted tracking-wider uppercase block mb-1">
                                        Transition in
                                    </label>
                                    <select
                                        data-testid={`segment-transition-${idx}`}
                                        value={seg.transition_in}
                                        onChange={(e) => updateSeg(idx, { transition_in: e.target.value })}
                                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-1 cursor-pointer"
                                    >
                                        {TRANSITIONS.map((t) => (
                                            <option key={t.value} value={t.value}>
                                                {t.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="col-span-2 flex justify-end gap-2 text-ink-muted">
                                    <button
                                        data-testid={`move-up-${idx}`}
                                        disabled={idx === 0}
                                        onClick={() => move(idx, -1)}
                                        className="disabled:opacity-30 hover:text-ink transition-colors duration-500"
                                    >
                                        <ArrowUp size={14} strokeWidth={1.25} />
                                    </button>
                                    <button
                                        data-testid={`move-down-${idx}`}
                                        disabled={idx === segments.length - 1}
                                        onClick={() => move(idx, 1)}
                                        className="disabled:opacity-30 hover:text-ink transition-colors duration-500"
                                    >
                                        <ArrowDown size={14} strokeWidth={1.25} />
                                    </button>
                                    <button
                                        data-testid={`remove-segment-${idx}`}
                                        onClick={() => removeSeg(idx)}
                                        className="hover:text-destructive transition-colors duration-500"
                                    >
                                        <X size={14} strokeWidth={1.25} />
                                    </button>
                                </div>
                            </li>
                        );
                    })}
                </ol>
            )}
        </div>
    );
}
