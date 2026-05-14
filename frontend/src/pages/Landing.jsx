import React from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";

const HERO_IMG =
    "https://static.prod-images.emergentagent.com/jobs/ada71dfb-d933-48e4-8342-e02998ea1886/images/dd9f794bcf0585db1e3cf89500b022e3c9fcd4bdd57b3540b4687d6f77a6aa93.png";

const PAPER_IMG =
    "https://static.prod-images.emergentagent.com/jobs/ada71dfb-d933-48e4-8342-e02998ea1886/images/a5c848b718b18ee28a1ce2f8a750a995a805e33495ec20cb527f899def414dae.png";

const Principle = ({ index, title, body }) => (
    <div
        data-testid={`principle-${index}`}
        className="grid grid-cols-12 gap-6 py-10 border-b hairline border-b-[rgba(26,25,24,0.12)]"
    >
        <div className="col-span-2 md:col-span-1 font-mono text-xs text-ink-muted pt-2">
            {String(index).padStart(2, "0")}
        </div>
        <h3 className="col-span-10 md:col-span-4 text-xl md:text-2xl font-serif text-ink">
            {title}
        </h3>
        <p className="col-span-12 md:col-span-7 text-sm md:text-base leading-relaxed text-ink-faded">
            {body}
        </p>
    </div>
);

export default function Landing() {
    return (
        <Layout>
            {/* Hero */}
            <section className="grid grid-cols-12 gap-10 items-end mb-28">
                <div className="col-span-12 md:col-span-7 reveal-1">
                    <p
                        data-testid="hero-eyebrow"
                        className="label-eyebrow mb-8"
                    >
                        A contemplative cinematic instrument
                    </p>
                    <h1
                        data-testid="hero-title"
                        className="font-serif text-5xl md:text-6xl lg:text-7xl leading-[1.05] text-ink"
                    >
                        Films that breathe.
                        <br />
                        <span className="italic text-ink-faded">
                            Not content that competes.
                        </span>
                    </h1>
                    <p
                        data-testid="hero-body"
                        className="mt-10 max-w-xl text-base md:text-lg leading-relaxed text-ink-faded"
                    >
                        Tattvashila is a quiet workshop for assembling slow,
                        observational cinema. Sequence your footage, weigh
                        each pause, lay narration over restraint, and render
                        a film grounded in <em>dharma</em> — not in the
                        algorithms of attention.
                    </p>
                    <div className="mt-12 flex items-center gap-6">
                        <Link
                            to="/projects"
                            data-testid="cta-begin"
                            className="inline-flex items-center px-6 py-3 bg-ink text-paper font-sans text-sm tracking-wide hover:bg-ink-faded transition-colors duration-700 ease-in-out"
                        >
                            Begin a work →
                        </Link>
                        <a
                            href="#principles"
                            data-testid="cta-principles"
                            className="text-sm text-ink-faded quiet-link"
                        >
                            Read the principles
                        </a>
                    </div>
                </div>
                <div className="col-span-12 md:col-span-5 reveal-2">
                    <div
                        className="relative aspect-[4/5] overflow-hidden border hairline border-[rgba(26,25,24,0.15)]"
                        data-testid="hero-still"
                    >
                        <img
                            src={HERO_IMG}
                            alt="A solitary figure walking into fog"
                            className="w-full h-full object-cover grayscale-[15%] contrast-[0.95]"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-paper/30 via-transparent to-transparent pointer-events-none" />
                    </div>
                    <p className="mt-4 text-xs text-ink-muted font-mono tracking-wider">
                        STILL · UNTITLED · 24FPS
                    </p>
                </div>
            </section>

            {/* Principles */}
            <section id="principles" className="mb-28">
                <div className="grid grid-cols-12 gap-6 mb-12">
                    <p className="col-span-2 md:col-span-1 label-eyebrow pt-2">
                        I.
                    </p>
                    <h2 className="col-span-10 md:col-span-7 font-serif text-3xl md:text-4xl text-ink">
                        Cinematic principles —{" "}
                        <span className="italic text-ink-faded">
                            held, not bent.
                        </span>
                    </h2>
                </div>
                <Principle
                    index={1}
                    title="Silence is part of storytelling."
                    body="The system treats pauses as first-class material. Black frames, room tone, the second between two thoughts — these are not absences. They are the architecture of attention."
                />
                <Principle
                    index={2}
                    title="Longer shots are acceptable."
                    body="Restrained editing means the eye is permitted to settle. The minimum clip length is generous on purpose. The shorter the cut, the louder the film argues with the viewer."
                />
                <Principle
                    index={3}
                    title="Stillness is emotionally powerful."
                    body="There are no zooms, no whips, no flashes. Only fades, slow dissolves, crossfades. The instrument refuses anything that performs urgency where none exists."
                />
                <Principle
                    index={4}
                    title="We never optimise for stimulation."
                    body="Trailer pacing, social-media rhythm, motivational beats — these are explicitly absent. The work is meant to be sat with, not scrolled past."
                />
            </section>

            {/* Capabilities */}
            <section className="mb-28">
                <div className="grid grid-cols-12 gap-6 mb-10">
                    <p className="col-span-2 md:col-span-1 label-eyebrow pt-2">
                        II.
                    </p>
                    <h2 className="col-span-10 md:col-span-7 font-serif text-3xl md:text-4xl text-ink">
                        The workshop.
                    </h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[rgba(26,25,24,0.12)] border hairline">
                    {[
                        {
                            t: "Timeline",
                            b: "Place clips with manual duration. Insert black-frame pauses as breath. Choose from four restrained transitions only.",
                        },
                        {
                            t: "Narration",
                            b: "Upload a recorded voice, or generate a calm, measured narration through OpenAI Text-to-Speech. The visuals follow the voice, never the inverse.",
                        },
                        {
                            t: "Ambience",
                            b: "Six curated atmospheric beds — room tone, wind, rain, forest, drone, paper — kept intentionally beneath the threshold of notice.",
                        },
                        {
                            t: "Grading",
                            b: "Muted palette, lowered contrast, soft warm highlights, optional film grain. No HDR, no oversaturation, no blockbuster sheen.",
                        },
                        {
                            t: "Render",
                            b: "Configurable per work: 1080p or 4K, 24fps by default. The output is an mp4 you keep — no platform owns it.",
                        },
                        {
                            t: "Pipeline",
                            b: "The same engine runs from a Python CLI: python -m pipeline render config.json. Integrable into archives, broadcasts, exhibitions.",
                        },
                    ].map((c, i) => (
                        <div
                            key={c.t}
                            data-testid={`capability-${i}`}
                            className="bg-paper p-10 hover:bg-paper-200 transition-colors duration-700 ease-in-out"
                        >
                            <p className="font-mono text-xs text-ink-muted mb-6">
                                {String(i + 1).padStart(2, "0")}
                            </p>
                            <h4 className="font-serif text-2xl text-ink mb-4">
                                {c.t}
                            </h4>
                            <p className="text-sm leading-relaxed text-ink-faded">
                                {c.b}
                            </p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Closing */}
            <section
                className="relative overflow-hidden border hairline border-[rgba(26,25,24,0.15)] mb-12"
                data-testid="closing-section"
            >
                <img
                    src={PAPER_IMG}
                    alt=""
                    aria-hidden
                    className="absolute inset-0 w-full h-full object-cover opacity-30"
                />
                <div className="relative px-10 md:px-20 py-20 md:py-28 text-center">
                    <p className="label-eyebrow mb-8">III. &nbsp; The intention</p>
                    <h2 className="font-serif text-3xl md:text-5xl lg:text-6xl text-ink leading-tight max-w-3xl mx-auto">
                        Not content. <span className="italic">A reflection</span>{" "}
                        on what civilisation is becoming.
                    </h2>
                    <p className="mt-10 max-w-xl mx-auto text-base text-ink-faded leading-relaxed">
                        Grounded in <em>Dharma</em>. Carried with integrity.
                        The film should outlast the feed it refuses to join.
                    </p>
                    <Link
                        to="/projects"
                        data-testid="closing-cta"
                        className="inline-block mt-12 text-sm text-ink underline underline-offset-8 decoration-1 decoration-ink/30 hover:decoration-ink quiet-link"
                    >
                        Enter the workshop →
                    </Link>
                </div>
            </section>
        </Layout>
    );
}
