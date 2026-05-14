import React from "react";

const Field = ({ label, children }) => (
    <div>
        <label className="label-eyebrow block mb-2">{label}</label>
        {children}
    </div>
);

export default function AmbiencePanel({ project, presets, assets, onChange }) {
    const a = project.ambient || {};
    const set = (patch) => onChange({ ...project, ambient: { ...a, ...patch } });

    const ambientUploads = assets.filter((x) => x.kind === "ambient");

    return (
        <div className="space-y-6" data-testid="ambience-panel">
            <Field label="Source">
                <div className="flex gap-1 text-xs">
                    {[
                        { v: "none", l: "None" },
                        { v: "builtin", l: "Curated" },
                        { v: "upload", l: "Upload" },
                    ].map((o) => (
                        <button
                            key={o.v}
                            data-testid={`ambient-source-${o.v}`}
                            onClick={() => set({ source: o.v })}
                            className={`px-3 py-1.5 transition-colors duration-500 ${
                                a.source === o.v
                                    ? "bg-ink text-paper"
                                    : "text-ink-muted hover:text-ink"
                            }`}
                        >
                            {o.l}
                        </button>
                    ))}
                </div>
            </Field>

            {a.source === "builtin" && (
                <Field label="Curated atmosphere">
                    <div className="space-y-2">
                        {presets.map((p) => (
                            <button
                                key={p.key}
                                data-testid={`ambient-pick-${p.key}`}
                                onClick={() => set({ builtin_key: p.key })}
                                className={`w-full text-left p-3 border hairline transition-colors duration-500 ${
                                    a.builtin_key === p.key
                                        ? "border-ink bg-paper-200"
                                        : "border-[rgba(26,25,24,0.1)] hover:border-ink/40"
                                }`}
                            >
                                <p className="text-sm text-ink">{p.label}</p>
                                <p className="text-xs text-ink-muted mt-0.5 italic">
                                    {p.description}
                                </p>
                            </button>
                        ))}
                    </div>
                </Field>
            )}

            {a.source === "upload" && (
                <Field label="Choose ambient file">
                    <select
                        data-testid="ambient-asset-select"
                        value={a.asset_id || ""}
                        onChange={(e) => set({ asset_id: e.target.value || null })}
                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2 cursor-pointer"
                    >
                        <option value="">— pick from library —</option>
                        {ambientUploads.map((x) => (
                            <option key={x.id} value={x.id}>
                                {x.original_filename}
                                {x.duration ? ` (${x.duration.toFixed(1)}s)` : ""}
                            </option>
                        ))}
                    </select>
                </Field>
            )}

            {a.source !== "none" && (
                <>
                    <Field label={`Volume · ${((a.volume ?? 0.3) * 100).toFixed(0)}%`}>
                        <input
                            data-testid="ambient-volume"
                            type="range"
                            min="0"
                            max="1"
                            step="0.05"
                            value={a.volume ?? 0.3}
                            onChange={(e) => set({ volume: parseFloat(e.target.value) })}
                            className="w-full accent-ink"
                        />
                    </Field>
                    <Field label={`Fade in · ${(a.fade_in ?? 3).toFixed(1)}s`}>
                        <input
                            data-testid="ambient-fade-in"
                            type="range"
                            min="0"
                            max="10"
                            step="0.5"
                            value={a.fade_in ?? 3}
                            onChange={(e) =>
                                set({ fade_in: parseFloat(e.target.value) })
                            }
                            className="w-full accent-ink"
                        />
                    </Field>
                    <Field label={`Fade out · ${(a.fade_out ?? 4).toFixed(1)}s`}>
                        <input
                            data-testid="ambient-fade-out"
                            type="range"
                            min="0"
                            max="10"
                            step="0.5"
                            value={a.fade_out ?? 4}
                            onChange={(e) =>
                                set({ fade_out: parseFloat(e.target.value) })
                            }
                            className="w-full accent-ink"
                        />
                    </Field>
                </>
            )}
        </div>
    );
}
