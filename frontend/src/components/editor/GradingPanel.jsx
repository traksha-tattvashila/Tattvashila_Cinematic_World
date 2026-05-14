import React from "react";

const Field = ({ label, children }) => (
    <div>
        <label className="label-eyebrow block mb-2">{label}</label>
        {children}
    </div>
);

const Toggle = ({ label, value, onChange, testid }) => (
    <label className="flex items-center justify-between cursor-pointer">
        <span className="text-sm text-ink">{label}</span>
        <button
            type="button"
            data-testid={testid}
            onClick={() => onChange(!value)}
            className={`w-10 h-5 border hairline transition-colors duration-500 relative ${
                value ? "bg-ink border-ink" : "bg-transparent border-[rgba(26,25,24,0.3)]"
            }`}
        >
            <span
                className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 transition-all duration-500 ${
                    value ? "right-1 bg-paper" : "left-1 bg-ink"
                }`}
            />
        </button>
    </label>
);

export default function GradingPanel({ project, onChange }) {
    const g = project.grading || {};
    const set = (patch) => onChange({ ...project, grading: { ...g, ...patch } });

    return (
        <div className="space-y-6" data-testid="grading-panel">
            <Toggle
                label="Muted palette"
                value={g.muted_palette ?? true}
                onChange={(v) => set({ muted_palette: v })}
                testid="toggle-muted"
            />
            {(g.muted_palette ?? true) && (
                <Field label={`Saturation · ${((g.saturation ?? 0.78) * 100).toFixed(0)}%`}>
                    <input
                        data-testid="grading-saturation"
                        type="range"
                        min="0.3"
                        max="1"
                        step="0.02"
                        value={g.saturation ?? 0.78}
                        onChange={(e) => set({ saturation: parseFloat(e.target.value) })}
                        className="w-full accent-ink"
                    />
                </Field>
            )}

            <Field label={`Contrast · ${((g.contrast ?? 0.95) * 100).toFixed(0)}%`}>
                <input
                    data-testid="grading-contrast"
                    type="range"
                    min="0.7"
                    max="1.1"
                    step="0.02"
                    value={g.contrast ?? 0.95}
                    onChange={(e) => set({ contrast: parseFloat(e.target.value) })}
                    className="w-full accent-ink"
                />
            </Field>

            <Toggle
                label="Warm highlights"
                value={g.warm_highlights ?? true}
                onChange={(v) => set({ warm_highlights: v })}
                testid="toggle-warm"
            />
            {(g.warm_highlights ?? true) && (
                <Field label={`Warmth · ${((g.warmth ?? 0.08) * 100).toFixed(0)}%`}>
                    <input
                        data-testid="grading-warmth"
                        type="range"
                        min="0"
                        max="0.2"
                        step="0.01"
                        value={g.warmth ?? 0.08}
                        onChange={(e) => set({ warmth: parseFloat(e.target.value) })}
                        className="w-full accent-ink"
                    />
                </Field>
            )}

            <Toggle
                label="Film grain"
                value={g.film_grain ?? true}
                onChange={(v) => set({ film_grain: v })}
                testid="toggle-grain"
            />
            {(g.film_grain ?? true) && (
                <Field label={`Grain intensity · ${((g.grain_intensity ?? 0.05) * 100).toFixed(0)}%`}>
                    <input
                        data-testid="grading-grain"
                        type="range"
                        min="0"
                        max="0.2"
                        step="0.01"
                        value={g.grain_intensity ?? 0.05}
                        onChange={(e) => set({ grain_intensity: parseFloat(e.target.value) })}
                        className="w-full accent-ink"
                    />
                </Field>
            )}

            <p className="text-[11px] text-ink-muted italic leading-relaxed pt-4 border-t hairline border-t-[rgba(26,25,24,0.1)]">
                Grading is applied frame-by-frame during render. It is intentionally restrained — the goal is a film that looks lived-in, not stylised.
            </p>
        </div>
    );
}
