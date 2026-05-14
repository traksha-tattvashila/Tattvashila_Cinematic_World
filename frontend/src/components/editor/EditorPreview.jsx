import React from "react";

/**
 * First-frame reference still. Composed at render time becomes the real film.
 *
 * Pure presentational. Receives the prepared `posterUrl` and render config.
 */
export default function EditorPreview({ posterUrl, width, height, fps }) {
    return (
        <div
            className="aspect-video bg-[#0f0e0d] relative overflow-hidden border hairline border-[rgba(26,25,24,0.2)]"
            data-testid="editor-preview"
        >
            {posterUrl ? (
                <video
                    key={posterUrl}
                    src={posterUrl}
                    muted
                    playsInline
                    className="w-full h-full object-contain"
                    style={{ filter: "saturate(0.78) contrast(0.95)" }}
                />
            ) : (
                <div className="w-full h-full flex items-center justify-center">
                    <p className="text-paper-200 font-serif italic text-lg opacity-60">
                        Stillness.
                    </p>
                </div>
            )}
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    background: "radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.4) 100%)",
                }}
            />
            <div className="absolute bottom-3 left-4 text-[10px] font-mono text-paper-200/70 tracking-widest">
                {width}×{height} · {fps}fps
            </div>
        </div>
    );
}
