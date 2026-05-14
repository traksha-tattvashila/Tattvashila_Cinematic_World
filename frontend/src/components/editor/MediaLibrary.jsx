import React, { useRef, useState } from "react";
import { http, endpoints, fileUrl } from "../../lib/api";
import { toast } from "sonner";
import { Upload, Film, Mic, Trash2 } from "lucide-react";

const KIND_LABELS = {
    clip: "Clips",
    narration: "Narration",
    ambient: "Ambience",
};

export default function MediaLibrary({
    assets,
    onUpload,
    onDelete,
    onPickClip,
    ambientPresets,
    onPickAmbientPreset,
}) {
    const [kind, setKind] = useState("clip");
    const [uploading, setUploading] = useState(false);
    const inputRef = useRef(null);

    const handleFiles = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setUploading(true);
        try {
            const fd = new FormData();
            fd.append("kind", kind);
            fd.append("file", file);
            const r = await http.post(endpoints.mediaUpload, fd, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            onUpload(r.data);
            toast.success(`${file.name} added`);
        } catch (e) {
            logError("media upload failed", e);
            toast.error(niceMessage(e, "Upload failed"));
        } finally {
            setUploading(false);
            if (inputRef.current) inputRef.current.value = "";
        }
    };

    const filtered = assets.filter((a) => a.kind === kind);

    return (
        <div
            className="border hairline border-[rgba(26,25,24,0.15)] bg-paper-50 flex flex-col h-full"
            data-testid="media-library"
        >
            <div className="border-b hairline border-b-[rgba(26,25,24,0.12)] p-5">
                <p className="label-eyebrow mb-3">Library</p>
                <div className="flex gap-1 text-xs">
                    {Object.entries(KIND_LABELS).map(([k, l]) => (
                        <button
                            key={k}
                            data-testid={`library-tab-${k}`}
                            onClick={() => setKind(k)}
                            className={`px-3 py-1.5 transition-colors duration-500 ${
                                kind === k
                                    ? "bg-ink text-paper"
                                    : "text-ink-muted hover:text-ink"
                            }`}
                        >
                            {l}
                        </button>
                    ))}
                </div>
            </div>

            <div className="p-5 border-b hairline border-b-[rgba(26,25,24,0.12)]">
                <label
                    htmlFor="file-input"
                    data-testid="upload-button"
                    className={`flex items-center justify-center gap-2 px-4 py-3 border border-dashed border-[rgba(26,25,24,0.3)] text-xs text-ink-faded hover:border-ink hover:text-ink cursor-pointer transition-colors duration-500 ${
                        uploading ? "opacity-60 pointer-events-none" : ""
                    }`}
                >
                    <Upload size={14} strokeWidth={1.25} />
                    {uploading ? "Uploading…" : `Upload ${KIND_LABELS[kind]}`}
                </label>
                <input
                    id="file-input"
                    ref={inputRef}
                    data-testid="file-input"
                    type="file"
                    onChange={handleFiles}
                    accept={
                        kind === "clip"
                            ? "video/*"
                            : "audio/*"
                    }
                    className="hidden"
                />
            </div>

            <div className="flex-1 overflow-y-auto">
                {kind === "ambient" && ambientPresets?.length > 0 && (
                    <div className="p-5 border-b hairline border-b-[rgba(26,25,24,0.12)]">
                        <p className="label-eyebrow mb-3">Curated presets</p>
                        <div className="space-y-2">
                            {ambientPresets.map((p) => (
                                <button
                                    key={p.key}
                                    data-testid={`preset-${p.key}`}
                                    onClick={() => onPickAmbientPreset(p)}
                                    className="w-full text-left p-3 border hairline border-[rgba(26,25,24,0.1)] hover:border-ink transition-colors duration-500 group"
                                >
                                    <p className="text-sm text-ink group-hover:text-ink">
                                        {p.label}
                                    </p>
                                    <p className="text-xs text-ink-muted mt-0.5 italic">
                                        {p.description}
                                    </p>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                <div className="p-5">
                    <p className="label-eyebrow mb-3">Your uploads</p>
                    {filtered.length === 0 ? (
                        <p className="text-xs text-ink-muted italic">
                            Nothing yet.
                        </p>
                    ) : (
                        <ul className="space-y-2">
                            {filtered.map((a) => (
                                <li
                                    key={a.id}
                                    data-testid={`asset-${a.id}`}
                                    className="border hairline border-[rgba(26,25,24,0.1)] p-3 group"
                                >
                                    <div className="flex items-start gap-2">
                                        <span className="text-ink-muted mt-0.5">
                                            {a.kind === "clip" ? (
                                                <Film size={14} strokeWidth={1.25} />
                                            ) : (
                                                <Mic size={14} strokeWidth={1.25} />
                                            )}
                                        </span>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs text-ink truncate">
                                                {a.original_filename}
                                            </p>
                                            <p className="text-[10px] text-ink-muted mt-0.5 font-mono tracking-wider">
                                                {a.duration ? `${a.duration.toFixed(1)}s` : "—"}
                                                {a.width ? ` · ${a.width}×${a.height}` : ""}
                                            </p>
                                            {a.kind === "clip" && (
                                                <button
                                                    data-testid={`add-clip-${a.id}`}
                                                    onClick={() => onPickClip(a)}
                                                    className="mt-2 text-[11px] text-ink-faded quiet-link"
                                                >
                                                    Place on timeline →
                                                </button>
                                            )}
                                        </div>
                                        <button
                                            data-testid={`delete-asset-${a.id}`}
                                            onClick={() => onDelete(a)}
                                            className="text-ink-soft hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                                        >
                                            <Trash2 size={13} strokeWidth={1.25} />
                                        </button>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    );
}
