import React, { memo, useState } from "react";
import { Check } from "lucide-react";

/**
 * A single ranked clip card. Memoised — the parent grid re-renders often
 * (selection toggles), but each card only repaints when its own props change.
 *
 * When `selected`, exposes inline trim-override inputs so the user can
 * pre-tune the start/duration before clicking "Import & assemble".
 */
function RetrievalClipCard({ clip, selected, trim, onToggle, onTrimChange }) {
    const [hovered, setHovered] = useState(false);
    const score = typeof clip.score === "number" ? Math.round(clip.score * 100) : null;
    const maxStart = Math.max(0, (clip.duration || 0) - 4);

    return (
        <div
            data-testid={`clip-${clip.provider}-${clip.external_id}`}
            onClick={() => onToggle(clip)}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            className={`relative border hairline cursor-pointer transition-all duration-500 ${
                selected
                    ? "border-ink bg-paper-200"
                    : "border-[rgba(26,25,24,0.12)] hover:border-ink/40"
            }`}
        >
            <div
                className={`absolute top-3 left-3 z-10 w-6 h-6 border hairline flex items-center justify-center transition-colors duration-500 ${
                    selected
                        ? "bg-ink border-ink text-paper"
                        : "bg-paper/80 border-[rgba(26,25,24,0.3)]"
                }`}
            >
                {selected && <Check size={12} strokeWidth={1.5} />}
            </div>
            {score !== null && (
                <div className="absolute top-3 right-3 z-10 bg-paper/90 border hairline border-[rgba(26,25,24,0.15)] px-2 py-0.5">
                    <span className="font-mono text-[11px] tracking-wider text-ink">
                        {score}
                    </span>
                </div>
            )}
            <div className="aspect-video bg-ink/5 relative overflow-hidden">
                {hovered && clip.preview_url ? (
                    <video
                        src={clip.preview_url}
                        autoPlay
                        muted
                        loop
                        playsInline
                        className="w-full h-full object-cover"
                        style={{ filter: "saturate(0.85) contrast(0.95)" }}
                    />
                ) : clip.thumbnail_url ? (
                    <img
                        src={clip.thumbnail_url}
                        alt=""
                        loading="lazy"
                        className="w-full h-full object-cover"
                        style={{ filter: "saturate(0.85) contrast(0.95)" }}
                    />
                ) : (
                    <div className="w-full h-full flex items-center justify-center text-ink-soft text-xs">
                        no preview
                    </div>
                )}
            </div>
            <div className="p-4">
                <div className="flex items-center justify-between text-[10px] font-mono tracking-widest uppercase text-ink-muted mb-2">
                    <span>{clip.provider}</span>
                    <span>
                        {clip.duration?.toFixed(1)}s · {clip.width}×{clip.height}
                    </span>
                </div>
                {clip.rationale && (
                    <p className="text-[13px] italic text-ink-faded leading-snug">
                        "{clip.rationale}"
                    </p>
                )}
                {clip.tags?.length > 0 && (
                    <p className="mt-3 text-[10px] text-ink-muted leading-relaxed">
                        {clip.tags.slice(0, 5).join(" · ")}
                    </p>
                )}
                {clip.author && (
                    <p className="mt-2 text-[10px] text-ink-soft tracking-wider">
                        by {clip.author}
                        {clip.source_url && (
                            <a
                                href={clip.source_url}
                                target="_blank"
                                rel="noreferrer noopener"
                                onClick={(e) => e.stopPropagation()}
                                className="ml-2 underline underline-offset-2 hover:text-ink"
                            >
                                source
                            </a>
                        )}
                    </p>
                )}

                {/* Trim override — only visible when the clip is selected. */}
                {selected && (
                    <div
                        data-testid={`trim-override-${clip.provider}-${clip.external_id}`}
                        className="mt-4 pt-3 border-t hairline border-t-[rgba(26,25,24,0.12)] grid grid-cols-2 gap-3"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div>
                            <label className="text-[10px] tracking-wider uppercase text-ink-muted block mb-1">
                                Start (s)
                            </label>
                            <input
                                data-testid={`trim-start-${clip.provider}-${clip.external_id}`}
                                type="number"
                                step="0.5"
                                min="0"
                                max={maxStart}
                                placeholder="auto"
                                value={trim?.trim_start ?? ""}
                                onChange={(e) =>
                                    onTrimChange(clip, {
                                        trim_start: e.target.value === "" ? null : parseFloat(e.target.value),
                                    })
                                }
                                className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-1"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] tracking-wider uppercase text-ink-muted block mb-1">
                                Duration (s)
                            </label>
                            <input
                                data-testid={`trim-duration-${clip.provider}-${clip.external_id}`}
                                type="number"
                                step="0.5"
                                min="2"
                                max="12"
                                placeholder="auto"
                                value={trim?.trim_duration ?? ""}
                                onChange={(e) =>
                                    onTrimChange(clip, {
                                        trim_duration: e.target.value === "" ? null : parseFloat(e.target.value),
                                    })
                                }
                                className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-1"
                            />
                        </div>
                        <p className="col-span-2 text-[10px] text-ink-soft italic">
                            Leave blank for adaptive trim (LLM, narration-aware).
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default memo(RetrievalClipCard, (prev, next) =>
    prev.selected === next.selected &&
    prev.clip.external_id === next.clip.external_id &&
    prev.clip.score === next.clip.score &&
    (prev.trim?.trim_start ?? null) === (next.trim?.trim_start ?? null) &&
    (prev.trim?.trim_duration ?? null) === (next.trim?.trim_duration ?? null),
);
