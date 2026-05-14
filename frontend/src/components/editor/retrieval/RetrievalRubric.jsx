import React from "react";

function Datum({ label, value, mono = false }) {
    return (
        <div>
            <p className="label-eyebrow mb-1">{label}</p>
            <p
                className={`text-ink ${mono ? "font-mono text-sm tracking-wider" : "text-base"}`}
            >
                {value || "—"}
            </p>
        </div>
    );
}

/**
 * Reads the rubric Claude produced for a scene. Pure presentational.
 */
export default function RetrievalRubric({ rubric }) {
    if (!rubric) return null;
    const restraintPct = Math.round((rubric.restraint_level || 0) * 100);
    return (
        <div
            data-testid="retrieval-rubric"
            className="px-6 sm:px-10 py-6 border-b hairline border-b-[rgba(26,25,24,0.1)] bg-paper-50"
        >
            <p className="label-eyebrow mb-4">The rubric</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-x-8 gap-y-4 text-sm">
                <Datum label="Tone" value={rubric.emotional_tone} />
                <Datum label="Pacing" value={rubric.pacing} mono />
                <Datum label="Environment" value={rubric.environment} />
                <Datum label="Atmosphere" value={rubric.atmosphere} />
                <Datum label="Restraint" value={`${restraintPct}%`} mono />
            </div>
            {rubric.rationale && (
                <p className="mt-5 text-[13px] italic text-ink-faded leading-relaxed max-w-3xl">
                    "{rubric.rationale}"
                </p>
            )}
            {rubric.search_queries?.length > 0 && (
                <div className="mt-5 flex flex-wrap gap-2">
                    {rubric.search_queries.map((q) => (
                        <span
                            key={q}
                            className="text-[11px] font-mono tracking-wider text-ink-muted px-2 py-1 border hairline border-[rgba(26,25,24,0.12)]"
                        >
                            {q}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}
