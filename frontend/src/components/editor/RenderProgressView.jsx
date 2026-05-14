import React, { useEffect } from "react";
import {
    VISIBLE_STAGES,
    stageMeta,
    stagePosition,
    formatBytes,
    formatDuration,
    TERMINAL_STATUSES,
} from "./renderStages";

/**
 * RenderProgressView — full-screen contemplative overlay shown while a film
 * is rendering. Strictly institutional: ivory paper, charcoal ink, no
 * spinners, no neon. The "motion" is the slow march of the active phase
 * dot down the rail, nothing else.
 */
export default function RenderProgressView({
    job,
    elapsedMs,
    etaMs,
    online,
    onClose,
    onViewResult,
}) {
    // Close on Escape
    useEffect(() => {
        const fn = (e) => {
            if (e.key === "Escape") onClose?.();
        };
        window.addEventListener("keydown", fn);
        return () => window.removeEventListener("keydown", fn);
    }, [onClose]);

    if (!job) return null;

    const meta = stageMeta(job.stage);
    const { index: activeIdx, sub: activeSub } = stagePosition(
        job.stage,
        job.progress || 0,
    );
    const terminal = TERMINAL_STATUSES.has(job.status);
    const failed = job.status === "failed";

    return (
        <div
            data-testid="render-progress-overlay"
            role="dialog"
            aria-modal="true"
            aria-label="Render progress"
            className="fixed inset-0 z-50 bg-paper text-ink overflow-y-auto paper-grain"
        >
            <div className="min-h-screen flex flex-col">
                {/* Header */}
                <header className="px-6 sm:px-14 py-6 sm:py-8 flex items-center justify-between border-b hairline border-b-[rgba(26,25,24,0.12)]">
                    <div className="flex items-baseline gap-4 sm:gap-6">
                        <span className="label-eyebrow" data-testid="render-overlay-eyebrow">
                            Tattvashila · Rendering
                        </span>
                        <span
                            data-testid="render-overlay-status"
                            className="text-[11px] font-mono tracking-widest uppercase text-ink-muted"
                        >
                            {failed ? "Interrupted" : terminal ? "Sealed" : "In progress"}
                        </span>
                    </div>
                    <button
                        data-testid="render-overlay-close"
                        onClick={onClose}
                        className="text-[11px] font-mono tracking-widest uppercase text-ink-faded hover:text-ink quiet-link"
                    >
                        Collapse ↓
                    </button>
                </header>

                {/* Body */}
                <main className="flex-1 px-6 sm:px-14 py-10 sm:py-16 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16">
                    {/* Left rail — phases */}
                    <section
                        className="lg:col-span-5"
                        data-testid="render-overlay-phases"
                    >
                        <p className="label-eyebrow mb-6">Phases</p>
                        <ol className="space-y-5">
                            {VISIBLE_STAGES.map((s, i) => {
                                const isActive = !terminal && i === activeIdx;
                                const isPast = i < activeIdx || (terminal && !failed);
                                const isPending = i > activeIdx;
                                return (
                                    <li
                                        key={s.key}
                                        data-testid={`render-phase-${s.key}`}
                                        data-state={isActive ? "active" : isPast ? "past" : "pending"}
                                        className="flex items-start gap-5"
                                    >
                                        <span
                                            aria-hidden
                                            className={`mt-2 inline-block w-2 h-2 rounded-full flex-shrink-0 transition-colors duration-700 ${
                                                isActive
                                                    ? "bg-ink"
                                                    : isPast
                                                        ? "bg-ink/40"
                                                        : "bg-ink/15"
                                            }`}
                                        />
                                        <div className="flex-1 min-w-0">
                                            <p
                                                className={`text-[11px] font-mono tracking-widest uppercase ${
                                                    isActive ? "text-ink" : "text-ink-muted"
                                                }`}
                                            >
                                                {s.eyebrow}
                                            </p>
                                            <p
                                                className={`font-serif text-lg sm:text-xl mt-1 ${
                                                    isActive
                                                        ? "text-ink"
                                                        : isPast
                                                            ? "text-ink-faded"
                                                            : "text-ink-muted/70"
                                                }`}
                                                style={{ fontFamily: "'Cormorant Garamond', Georgia, serif" }}
                                            >
                                                {s.title}
                                            </p>
                                            {isActive && (
                                                <div
                                                    className="h-px bg-[rgba(26,25,24,0.08)] mt-3 overflow-hidden"
                                                    data-testid={`render-phase-bar-${s.key}`}
                                                >
                                                    <div
                                                        className="h-full bg-ink transition-all duration-700 ease-out"
                                                        style={{
                                                            width: `${Math.round(activeSub * 100)}%`,
                                                        }}
                                                    />
                                                </div>
                                            )}
                                            {isPending && (
                                                <p className="text-xs text-ink-muted/60 mt-1 italic">
                                                    Not yet begun.
                                                </p>
                                            )}
                                        </div>
                                    </li>
                                );
                            })}
                        </ol>
                    </section>

                    {/* Right — focal pane */}
                    <section className="lg:col-span-7 flex flex-col">
                        <div className="flex-1 flex flex-col justify-center max-w-2xl">
                            <p
                                className="label-eyebrow"
                                data-testid="render-overlay-active-eyebrow"
                            >
                                {meta.eyebrow}
                            </p>
                            <h1
                                className="font-serif text-4xl sm:text-5xl lg:text-6xl leading-tight mt-4 mb-6"
                                style={{
                                    fontFamily: "'Cormorant Garamond', Georgia, serif",
                                    fontWeight: 300,
                                }}
                                data-testid="render-overlay-title"
                            >
                                {failed ? "The render did not complete." : meta.title}.
                            </h1>
                            <p
                                className="text-base text-ink-faded italic leading-relaxed max-w-xl"
                                data-testid="render-overlay-whisper"
                            >
                                {failed
                                    ? job.error || "Something resisted. The film was not sealed."
                                    : meta.whisper}
                            </p>

                            {/* Master progress bar */}
                            <div className="mt-12">
                                <div className="flex items-baseline justify-between mb-3">
                                    <span className="label-eyebrow">Overall</span>
                                    <span
                                        className="text-xs font-mono text-ink-muted"
                                        data-testid="render-overlay-percent"
                                    >
                                        {Math.round((job.progress || 0) * 100)}%
                                    </span>
                                </div>
                                <div className="h-px bg-[rgba(26,25,24,0.12)] overflow-hidden">
                                    <div
                                        data-testid="render-overlay-master-bar"
                                        className={`h-full transition-all duration-700 ease-out ${
                                            failed ? "bg-destructive" : "bg-ink"
                                        }`}
                                        style={{
                                            width: `${Math.round((job.progress || 0) * 100)}%`,
                                        }}
                                    />
                                </div>
                            </div>

                            {/* Meta grid */}
                            <dl className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-6 text-sm">
                                <div data-testid="render-overlay-elapsed">
                                    <dt className="label-eyebrow mb-1.5">Elapsed</dt>
                                    <dd className="font-mono">{formatDuration(elapsedMs / 1000)}</dd>
                                </div>
                                <div data-testid="render-overlay-eta">
                                    <dt className="label-eyebrow mb-1.5">Remaining</dt>
                                    <dd className="font-mono">
                                        {terminal
                                            ? "—"
                                            : etaMs
                                                ? `≈ ${formatDuration(etaMs / 1000)}`
                                                : "—"}
                                    </dd>
                                </div>
                                <div data-testid="render-overlay-size">
                                    <dt className="label-eyebrow mb-1.5">Master file</dt>
                                    <dd className="font-mono">
                                        {formatBytes(job.output_size_bytes)}
                                    </dd>
                                </div>
                                <div data-testid="render-overlay-queue">
                                    <dt className="label-eyebrow mb-1.5">Queue ahead</dt>
                                    <dd className="font-mono">
                                        {job.status === "queued"
                                            ? job.queue_position ?? 0
                                            : "—"}
                                    </dd>
                                </div>
                            </dl>

                            {/* Network awareness */}
                            <div
                                className="mt-10 flex items-center gap-3 text-xs text-ink-muted"
                                data-testid="render-overlay-network"
                            >
                                <span
                                    aria-hidden
                                    className={`inline-block w-1.5 h-1.5 rounded-full ${
                                        online ? "bg-ink/40" : "bg-destructive"
                                    }`}
                                />
                                <span className="font-mono tracking-wider uppercase">
                                    {online ? "Network · steady" : "Network · offline"}
                                </span>
                                {!online && (
                                    <span className="italic text-ink-muted/80">
                                        — the render continues on the server; only the live update is paused.
                                    </span>
                                )}
                            </div>

                            {terminal && (
                                <div
                                    className="mt-12 pt-8 border-t hairline border-t-[rgba(26,25,24,0.12)] flex flex-wrap items-center gap-6"
                                    data-testid="render-overlay-terminal"
                                >
                                    {!failed && (
                                        <button
                                            data-testid="render-overlay-view"
                                            onClick={onViewResult}
                                            className="px-5 py-3 bg-ink text-paper text-xs tracking-widest uppercase hover:bg-ink-faded transition-colors duration-700"
                                        >
                                            View the film
                                        </button>
                                    )}
                                    <button
                                        data-testid="render-overlay-dismiss"
                                        onClick={onClose}
                                        className="text-xs font-mono tracking-widest uppercase text-ink-faded quiet-link"
                                    >
                                        Return to the workshop
                                    </button>
                                </div>
                            )}
                        </div>
                    </section>
                </main>

                {/* Quiet footer */}
                <footer className="px-6 sm:px-14 py-5 border-t hairline border-t-[rgba(26,25,24,0.12)] flex items-center justify-between text-[11px] font-mono tracking-widest uppercase text-ink-muted">
                    <span>Job · {job.id?.slice(0, 8)}</span>
                    <span>Press Esc to collapse</span>
                </footer>
            </div>
        </div>
    );
}
