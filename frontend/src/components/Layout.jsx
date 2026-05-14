import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Layout({ children, wide = false }) {
    const loc = useLocation();
    const isActive = (path) =>
        path === "/" ? loc.pathname === "/" : loc.pathname.startsWith(path);

    return (
        <div className="min-h-screen bg-paper text-ink">
            <header
                data-testid="site-header"
                className="border-b hairline border-b-[rgba(26,25,24,0.12)] bg-paper/95 backdrop-blur-sm sticky top-0 z-40"
            >
                <div className="max-w-[1600px] mx-auto px-8 md:px-12 py-6 flex items-center justify-between">
                    <Link
                        to="/"
                        data-testid="nav-home"
                        className="flex items-baseline gap-3 group"
                    >
                        <span className="font-serif text-2xl md:text-3xl text-ink tracking-tight">
                            Tattvashila
                        </span>
                        <span className="label-eyebrow hidden sm:inline">
                            तत्त्वशिला &nbsp;·&nbsp; Cinematic Foundations
                        </span>
                    </Link>
                    <nav className="flex items-center gap-8 text-sm text-ink-faded">
                        <Link
                            to="/"
                            data-testid="nav-foundations"
                            className={`quiet-link ${isActive("/") && "text-ink"}`}
                        >
                            Foundations
                        </Link>
                        <Link
                            to="/projects"
                            data-testid="nav-projects"
                            className={`quiet-link ${isActive("/projects") && "text-ink"}`}
                        >
                            Works
                        </Link>
                    </nav>
                </div>
            </header>

            <main
                className={`${wide ? "" : "max-w-[1200px] mx-auto px-8 md:px-12"} py-12 md:py-20 animate-fade-in`}
            >
                {children}
            </main>

            <footer
                data-testid="site-footer"
                className="border-t hairline border-t-[rgba(26,25,24,0.12)] mt-24"
            >
                <div className="max-w-[1600px] mx-auto px-8 md:px-12 py-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs text-ink-muted">
                    <span className="label-eyebrow">
                        Tattvashila · A contemplative cinematic instrument
                    </span>
                    <span className="font-mono text-[10px] tracking-widest text-ink-soft">
                        v0.1 · ग्राउण्डेड इन धर्म
                    </span>
                </div>
            </footer>
        </div>
    );
}
