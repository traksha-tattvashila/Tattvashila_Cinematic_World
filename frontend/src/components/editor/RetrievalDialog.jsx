import React, { useEffect, useMemo, useState } from "react";
import { X, Sparkles, Search } from "lucide-react";

import useRetrieval from "../../hooks/useRetrieval";
import RetrievalRubric from "./retrieval/RetrievalRubric";
import RetrievalClipCard from "./retrieval/RetrievalClipCard";

const EXAMPLE_SCENES = [
    "Quiet exhausted woman scrolling phone before sunrise",
    "Crowded metro with emotionally disconnected passengers",
    "Contemplative forest pathway at dawn",
    "Empty office windows reflecting a grey city",
];

const REASON_COPY = {
    no_results_from_providers:
        "Pexels and Pixabay returned nothing for these queries. The field is empty — try a softer phrasing below.",
    filtered_by_contemplative_mode:
        "Contemplative Mode rejected every result. The field returned footage, but none scored above the restraint threshold.",
    no_matches:
        "Nothing in the field was close to your description. Try a calmer phrasing below.",
};

export default function RetrievalDialog({ open, project, onClose, onAssembled }) {
    const [description, setDescription] = useState("");
    const [contemplativeMode, setContemplativeMode] = useState(true);
    const [useNarration, setUseNarration] = useState(false);

    const {
        phase, rubric, clips, selected, suggestions, reason,
        search, widenThreshold, toggleSelect, isSelected,
        getTrim, setTrim, assemble, reset,
        PHASES,
    } = useRetrieval({
        projectId: project?.id,
        onAssembled: (updated) => {
            onAssembled?.(updated);
            onClose?.();
            setTimeout(reset, 500);
        },
    });

    const hasNarrationText =
        project?.narration?.source === "tts" && !!project?.narration?.tts_text;

    useEffect(() => {
        if (open && project && !description) {
            setDescription(project.description || project.subtitle || "");
            setUseNarration(hasNarrationText);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open]);

    const canSearch = useMemo(
        () => description.trim().length > 4
            && phase !== PHASES.ANALYZING
            && phase !== PHASES.ASSEMBLING,
        [description, phase, PHASES.ANALYZING, PHASES.ASSEMBLING],
    );

    if (!open) return null;

    const onSearch = () => {
        if (!canSearch) return;
        search({
            description,
            contemplativeMode,
            narrationText: useNarration ? project?.narration?.tts_text : null,
        });
    };

    const onWiden = () => {
        widenThreshold({
            description,
            narrationText: useNarration ? project?.narration?.tts_text : null,
        });
        setContemplativeMode(false);
    };

    const onAssemble = () =>
        assemble({
            pacing: rubric?.pacing || "slow",
            transition: "crossfade",
            atmosphere: rubric?.atmosphere || "",
        });

    const showFallback =
        phase === PHASES.SEARCHED && clips.length === 0 && rubric;

    return (
        <div
            data-testid="retrieval-dialog"
            className="fixed inset-0 z-50 bg-ink/40 backdrop-blur-sm animate-fade-in flex items-stretch justify-center"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div
                className="bg-paper w-full max-w-[1280px] my-2 sm:my-8 mx-2 sm:mx-6 border hairline border-[rgba(26,25,24,0.2)] flex flex-col overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="border-b hairline border-b-[rgba(26,25,24,0.12)] px-6 sm:px-10 py-5 sm:py-6 flex items-baseline justify-between gap-4">
                    <div className="min-w-0">
                        <p className="label-eyebrow mb-2 flex items-center gap-2">
                            <Sparkles size={12} strokeWidth={1.25} /> Atmospheric Retrieval
                        </p>
                        <h2 className="font-serif text-2xl sm:text-3xl text-ink leading-tight">
                            What does the scene <em className="text-ink-faded">feel</em> like?
                        </h2>
                    </div>
                    <button
                        data-testid="retrieval-close"
                        onClick={onClose}
                        className="text-ink-muted hover:text-ink transition-colors duration-500 p-1 shrink-0"
                    >
                        <X size={18} strokeWidth={1.25} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    <div className="px-6 sm:px-10 py-6 sm:py-8 border-b hairline border-b-[rgba(26,25,24,0.1)]">
                        <textarea
                            data-testid="retrieval-description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="A scene. An emotional context. A texture in your head. Describe it as you would to a cinematographer over tea."
                            rows={3}
                            className="w-full bg-transparent border-0 border-b border-[rgba(26,25,24,0.18)] focus:border-ink outline-none py-3 font-serif italic text-xl sm:text-2xl text-ink leading-relaxed placeholder:text-ink-soft transition-colors duration-500 resize-none"
                        />

                        <div className="flex flex-wrap gap-2 mt-6">
                            {EXAMPLE_SCENES.map((s) => (
                                <button
                                    key={s}
                                    data-testid={`example-scene-${s.slice(0,12).replace(/\s+/g,'-').toLowerCase()}`}
                                    onClick={() => setDescription(s)}
                                    className="text-[11px] tracking-wider uppercase text-ink-muted px-3 py-1.5 border hairline border-[rgba(26,25,24,0.12)] hover:border-ink hover:text-ink transition-colors duration-500"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>

                        <div className="mt-8 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                            <div className="flex flex-col gap-3">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        data-testid="contemplative-mode-toggle"
                                        type="checkbox"
                                        checked={contemplativeMode}
                                        onChange={(e) => setContemplativeMode(e.target.checked)}
                                        className="w-4 h-4 accent-ink"
                                    />
                                    <span className="text-sm text-ink">Contemplative mode</span>
                                    <span className="text-[11px] text-ink-muted italic">
                                        bias toward stillness, hard-filter chaos
                                    </span>
                                </label>
                                {hasNarrationText && (
                                    <label className="flex items-center gap-3 cursor-pointer">
                                        <input
                                            data-testid="narration-sync-toggle"
                                            type="checkbox"
                                            checked={useNarration}
                                            onChange={(e) => setUseNarration(e.target.checked)}
                                            className="w-4 h-4 accent-ink"
                                        />
                                        <span className="text-sm text-ink">Sync with narration script</span>
                                        <span className="text-[11px] text-ink-muted italic">
                                            shape retrieval to fit the voice
                                        </span>
                                    </label>
                                )}
                            </div>
                            <button
                                data-testid="retrieval-search-btn"
                                onClick={onSearch}
                                disabled={!canSearch}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-ink text-paper text-sm tracking-wider hover:bg-ink-faded transition-colors duration-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Search size={14} strokeWidth={1.25} />
                                {phase === PHASES.ANALYZING ? "Reading the scene…" : "Analyse & retrieve →"}
                            </button>
                        </div>
                    </div>

                    <RetrievalRubric rubric={rubric} />

                    {clips.length > 0 && (
                        <div className="px-6 sm:px-10 py-8" data-testid="retrieval-results">
                            <div className="flex items-baseline justify-between mb-6">
                                <p className="label-eyebrow">
                                    {clips.length} ranked clip{clips.length === 1 ? "" : "s"}
                                </p>
                                <p className="text-[11px] font-mono text-ink-muted tracking-wider hidden sm:inline">
                                    SORTED · RESTRAINT-FIRST
                                </p>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                                {clips.map((c) => (
                                    <RetrievalClipCard
                                        key={`${c.provider}|${c.external_id}`}
                                        clip={c}
                                        selected={isSelected(c)}
                                        trim={getTrim(c)}
                                        onToggle={toggleSelect}
                                        onTrimChange={setTrim}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {showFallback && (
                        <div className="px-6 sm:px-10 py-12 sm:py-14 max-w-3xl" data-testid="retrieval-empty">
                            <p className="label-eyebrow mb-4">An empty field</p>
                            <h3 className="font-serif text-2xl sm:text-3xl text-ink-faded italic mb-5 leading-tight">
                                Nothing measured up.
                            </h3>
                            <p className="text-sm text-ink-faded leading-relaxed mb-8">
                                {REASON_COPY[reason] || REASON_COPY.no_matches}
                            </p>

                            {suggestions.length > 0 && (
                                <div className="mb-8">
                                    <p className="label-eyebrow mb-3">Gentler phrasings</p>
                                    <div className="flex flex-wrap gap-2">
                                        {suggestions.map((s) => (
                                            <button
                                                key={s}
                                                data-testid={`suggestion-${s.slice(0,12).replace(/\s+/g,'-').toLowerCase()}`}
                                                onClick={() => {
                                                    setDescription(s);
                                                    setTimeout(() => {
                                                        search({
                                                            description: s,
                                                            contemplativeMode,
                                                            narrationText: useNarration
                                                                ? project?.narration?.tts_text
                                                                : null,
                                                        });
                                                    }, 0);
                                                }}
                                                className="text-[11px] tracking-wider uppercase text-ink-muted px-3 py-1.5 border hairline border-[rgba(26,25,24,0.12)] hover:border-ink hover:text-ink transition-colors duration-500"
                                            >
                                                {s}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {reason === "filtered_by_contemplative_mode" && (
                                <button
                                    data-testid="widen-threshold-btn"
                                    onClick={onWiden}
                                    className="px-5 py-2.5 border hairline border-ink text-xs tracking-wider text-ink hover:bg-ink hover:text-paper transition-colors duration-700"
                                >
                                    Widen the threshold (turn off Contemplative Mode)
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {clips.length > 0 && (
                    <div className="border-t hairline border-t-[rgba(26,25,24,0.12)] px-6 sm:px-10 py-4 sm:py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-paper">
                        <p className="text-sm text-ink-faded">
                            {selected.size === 0
                                ? "Select the clips that hold the feeling."
                                : `${selected.size} selected — will be trimmed and woven onto the timeline.`}
                        </p>
                        <button
                            data-testid="retrieval-assemble-btn"
                            onClick={onAssemble}
                            disabled={selected.size === 0 || phase === PHASES.ASSEMBLING}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-ink text-paper text-sm tracking-wider hover:bg-ink-faded transition-colors duration-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {phase === PHASES.ASSEMBLING ? "Weaving into timeline…" : "Import & assemble →"}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
