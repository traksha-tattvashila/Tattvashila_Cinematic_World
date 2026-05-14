import React, { useState } from "react";
import { http, endpoints } from "../../lib/api";
import { logError, niceMessage } from "../../lib/log";
import { toast } from "sonner";

const Field = ({ label, children }) => (
    <div>
        <label className="label-eyebrow block mb-2">{label}</label>
        {children}
    </div>
);

export default function NarrationPanel({ project, voices, assets, onChange, onAssetAdded }) {
    const n = project.narration || {};
    const set = (patch) =>
        onChange({ ...project, narration: { ...n, ...patch } });

    const [text, setText] = useState(n.tts_text || "");
    const [generating, setGenerating] = useState(false);

    const narrationAssets = assets.filter((a) => a.kind === "narration");

    const generate = async () => {
        if (!text.trim()) return toast.error("Write something to be spoken");
        setGenerating(true);
        try {
            const r = await http.post(endpoints.narrationTTS, {
                text: text.trim(),
                voice: n.tts_voice || "echo",
                model: n.tts_model || "tts-1-hd",
                speed: n.tts_speed ?? 0.95,
            });
            onAssetAdded(r.data);
            set({
                source: "tts",
                asset_id: r.data.id,
                tts_text: text.trim(),
            });
            toast.success("Narration generated");
        } catch (e) {
            logError("tts generate failed", e);
            toast.error(niceMessage(e, "Generation failed"));
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="space-y-6" data-testid="narration-panel">
            <Field label="Source">
                <div className="flex gap-1 text-xs">
                    {[
                        { v: "none", l: "None" },
                        { v: "upload", l: "Upload" },
                        { v: "tts", l: "Generate" },
                    ].map((o) => (
                        <button
                            key={o.v}
                            data-testid={`narration-source-${o.v}`}
                            onClick={() => set({ source: o.v })}
                            className={`px-3 py-1.5 transition-colors duration-500 ${
                                n.source === o.v
                                    ? "bg-ink text-paper"
                                    : "text-ink-muted hover:text-ink"
                            }`}
                        >
                            {o.l}
                        </button>
                    ))}
                </div>
            </Field>

            {n.source === "upload" && (
                <Field label="Choose narration file">
                    <select
                        data-testid="narration-asset-select"
                        value={n.asset_id || ""}
                        onChange={(e) => set({ asset_id: e.target.value || null })}
                        className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2 cursor-pointer"
                    >
                        <option value="">— pick from library —</option>
                        {narrationAssets.map((a) => (
                            <option key={a.id} value={a.id}>
                                {a.original_filename}
                                {a.duration ? ` (${a.duration.toFixed(1)}s)` : ""}
                            </option>
                        ))}
                    </select>
                </Field>
            )}

            {n.source === "tts" && (
                <>
                    <Field label="Voice">
                        <select
                            data-testid="narration-voice-select"
                            value={n.tts_voice || "echo"}
                            onChange={(e) => set({ tts_voice: e.target.value })}
                            className="w-full bg-transparent border-b border-[rgba(26,25,24,0.2)] focus:border-ink outline-none text-sm py-2 cursor-pointer"
                        >
                            {voices.map((v) => (
                                <option key={v.key} value={v.key}>
                                    {v.label}
                                </option>
                            ))}
                        </select>
                    </Field>
                    <Field label="Model">
                        <div className="flex gap-1 text-xs">
                            {["tts-1-hd", "tts-1"].map((m) => (
                                <button
                                    key={m}
                                    data-testid={`narration-model-${m}`}
                                    onClick={() => set({ tts_model: m })}
                                    className={`px-3 py-1.5 transition-colors duration-500 ${
                                        (n.tts_model || "tts-1-hd") === m
                                            ? "bg-ink text-paper"
                                            : "text-ink-muted hover:text-ink"
                                    }`}
                                >
                                    {m === "tts-1-hd" ? "HD (slow)" : "Fast"}
                                </button>
                            ))}
                        </div>
                    </Field>
                    <Field label={`Speed · ${(n.tts_speed ?? 0.95).toFixed(2)}×`}>
                        <input
                            data-testid="narration-speed"
                            type="range"
                            min="0.6"
                            max="1.2"
                            step="0.05"
                            value={n.tts_speed ?? 0.95}
                            onChange={(e) =>
                                set({ tts_speed: parseFloat(e.target.value) })
                            }
                            className="w-full accent-ink"
                        />
                    </Field>
                    <Field label="Script">
                        <textarea
                            data-testid="narration-text"
                            value={text}
                            onChange={(e) => setText(e.target.value)}
                            placeholder="The voice begins here. Keep it measured. Allow the breath to land between sentences…"
                            rows={6}
                            maxLength={4096}
                            className="w-full bg-transparent border border-[rgba(26,25,24,0.18)] focus:border-ink outline-none p-3 text-sm font-serif italic text-ink-faded leading-relaxed resize-none transition-colors duration-500"
                        />
                        <p className="text-[10px] text-ink-muted font-mono mt-2 tracking-wider">
                            {text.length} / 4096
                        </p>
                    </Field>
                    <button
                        data-testid="generate-narration-btn"
                        onClick={generate}
                        disabled={generating}
                        className="px-5 py-2.5 bg-ink text-paper text-xs tracking-wider hover:bg-ink-faded transition-colors duration-700 disabled:opacity-50"
                    >
                        {generating ? "Synthesising voice…" : "Generate narration →"}
                    </button>
                </>
            )}

            {n.source !== "none" && (
                <>
                    <Field label={`Lead-in silence · ${(n.offset_seconds ?? 1.5).toFixed(1)}s`}>
                        <input
                            data-testid="narration-offset"
                            type="range"
                            min="0"
                            max="8"
                            step="0.5"
                            value={n.offset_seconds ?? 1.5}
                            onChange={(e) =>
                                set({ offset_seconds: parseFloat(e.target.value) })
                            }
                            className="w-full accent-ink"
                        />
                    </Field>
                    <Field label={`Volume · ${((n.volume ?? 1) * 100).toFixed(0)}%`}>
                        <input
                            data-testid="narration-volume"
                            type="range"
                            min="0"
                            max="1.2"
                            step="0.05"
                            value={n.volume ?? 1}
                            onChange={(e) =>
                                set({ volume: parseFloat(e.target.value) })
                            }
                            className="w-full accent-ink"
                        />
                    </Field>
                </>
            )}
        </div>
    );
}
