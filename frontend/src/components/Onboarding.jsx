import React, { useEffect, useState } from "react";

const STORAGE_KEY = "tattva.onboarded";

const SLIDES = [
    {
        eyebrow: "I. The Workshop",
        title: "A quiet instrument for slow cinema.",
        body: "Tattvashila is built for restraint, not virality. You place clips on a timeline, breathe in pauses, lay narration on top, and render a film that respects attention.",
    },
    {
        eyebrow: "II. Manual editing",
        title: "Upload, sequence, refine.",
        body: "Upload your own clips, narration, and ambience from the library on the left. Place them on the timeline. Choose fade, crossfade, or dissolve transitions — nothing flashier exists, by design.",
    },
    {
        eyebrow: "III. Atmospheric retrieval",
        title: "Find footage that feels right.",
        body: "Click 'Atmospheric retrieval' in the header. Describe the scene as you would to a cinematographer. Claude composes a rubric; Pexels and Pixabay are queried; the results are ranked for cinematic restraint.",
    },
    {
        eyebrow: "IV. Contemplative mode",
        title: "Hard-filter the chaos.",
        body: "When Contemplative Mode is on, anything that scores below the restraint threshold is rejected. Your timeline never accidentally inherits vlog energy. Turn it off only when you need the wider field.",
    },
    {
        eyebrow: "V. Rendering",
        title: "The film is composed at render time.",
        body: "Pick a render preset, press 'Render the film', and the system composes clips, narration, ambient bed, and grading into a single MP4. The output is yours — no platform owns it.",
    },
];

/**
 * One-time, restrained onboarding overlay.
 *
 * Triggers on the editor's first visit (localStorage flag). Five quiet
 * slides — institutional language, paper-cream and ink only. Closable at
 * any time. Re-openable from the help link in the editor header (TODO).
 */
export default function Onboarding({ forceOpen = false, onClose }) {
    const [open, setOpen] = useState(false);
    const [i, setI] = useState(0);

    useEffect(() => {
        if (forceOpen) {
            setOpen(true);
            return;
        }
        try {
            if (!window.localStorage.getItem(STORAGE_KEY)) {
                setOpen(true);
            }
        } catch {
            /* ignore */
        }
    }, [forceOpen]);

    const finish = () => {
        try {
            window.localStorage.setItem(STORAGE_KEY, new Date().toISOString());
        } catch {
            /* ignore */
        }
        setOpen(false);
        setI(0);
        onClose?.();
    };

    if (!open) return null;
    const slide = SLIDES[i];
    const isLast = i === SLIDES.length - 1;

    return (
        <div
            data-testid="onboarding-overlay"
            className="fixed inset-0 z-[60] bg-ink/45 backdrop-blur-sm flex items-center justify-center px-4 sm:px-8 animate-fade-in"
            onClick={(e) => { if (e.target === e.currentTarget) finish(); }}
        >
            <div
                className="bg-paper max-w-2xl w-full border hairline border-[rgba(26,25,24,0.2)]"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="px-8 sm:px-12 py-10 sm:py-14">
                    <p className="label-eyebrow mb-6" data-testid="onboarding-eyebrow">{slide.eyebrow}</p>
                    <h2
                        className="font-serif text-3xl sm:text-4xl text-ink leading-tight mb-6"
                        data-testid="onboarding-title"
                    >
                        {slide.title}
                    </h2>
                    <p className="text-base text-ink-faded leading-relaxed">
                        {slide.body}
                    </p>
                </div>
                <div className="border-t hairline border-t-[rgba(26,25,24,0.12)] px-8 sm:px-12 py-5 flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                        {SLIDES.map((_, idx) => (
                            <span
                                key={idx}
                                className={`w-6 h-px transition-colors duration-700 ${
                                    idx === i ? "bg-ink" : "bg-[rgba(26,25,24,0.18)]"
                                }`}
                            />
                        ))}
                    </div>
                    <div className="flex items-center gap-3 sm:gap-5">
                        <button
                            data-testid="onboarding-skip"
                            onClick={finish}
                            className="text-xs text-ink-muted quiet-link tracking-wider uppercase"
                        >
                            Skip
                        </button>
                        {!isLast ? (
                            <button
                                data-testid="onboarding-next"
                                onClick={() => setI((n) => n + 1)}
                                className="px-5 py-2 bg-ink text-paper text-xs tracking-wider hover:bg-ink-faded transition-colors duration-700"
                            >
                                Next →
                            </button>
                        ) : (
                            <button
                                data-testid="onboarding-begin"
                                onClick={finish}
                                className="px-5 py-2 bg-ink text-paper text-xs tracking-wider hover:bg-ink-faded transition-colors duration-700"
                            >
                                Begin →
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
