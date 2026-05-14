import React from "react";
import { Link } from "react-router-dom";
import { ChevronLeft, Save, Sparkles } from "lucide-react";

/**
 * Editor header — title, save state, retrieval shortcut.
 *
 * Pure presentational; all state lives in the parent Editor page.
 */
export default function EditorHeader({
    title, subtitle,
    saving, dirty,
    onTitleChange,
    onSave,
    onOpenRetrieval,
}) {
    return (
        <header className="border-b hairline border-b-[rgba(26,25,24,0.12)] bg-paper/95 backdrop-blur-sm sticky top-0 z-30">
            <div className="px-4 sm:px-6 md:px-10 py-4 md:py-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-3 sm:gap-6 min-w-0 flex-1">
                    <Link
                        to="/projects"
                        data-testid="back-to-projects"
                        className="text-ink-muted hover:text-ink quiet-link flex items-center gap-1 shrink-0"
                    >
                        <ChevronLeft size={16} strokeWidth={1.25} />
                        <span className="text-xs tracking-wider uppercase">Works</span>
                    </Link>
                    <div className="min-w-0 flex-1">
                        <input
                            data-testid="editor-title"
                            value={title}
                            onChange={(e) => onTitleChange(e.target.value)}
                            className="font-serif text-xl md:text-2xl lg:text-3xl text-ink bg-transparent outline-none border-b border-transparent focus:border-ink/30 transition-colors duration-500 w-full"
                        />
                        {subtitle && (
                            <p className="text-xs text-ink-muted italic mt-1 truncate">
                                {subtitle}
                            </p>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2 sm:gap-4">
                    <button
                        data-testid="open-retrieval-btn"
                        onClick={onOpenRetrieval}
                        aria-label="Atmospheric retrieval"
                        className="flex items-center gap-1.5 px-3 sm:px-4 py-2 text-xs text-ink-faded border hairline border-[rgba(26,25,24,0.18)] hover:border-ink hover:text-ink transition-colors duration-500"
                    >
                        <Sparkles size={13} strokeWidth={1.25} />
                        <span className="hidden sm:inline" aria-hidden="true">Atmospheric retrieval</span>
                        <span className="sm:hidden" aria-hidden="true">Retrieve</span>
                    </button>
                    <span
                        data-testid="editor-save-status"
                        className="text-[11px] font-mono text-ink-muted tracking-wider uppercase hidden sm:inline"
                    >
                        {saving ? "Saving…" : dirty ? "Unsaved" : "Saved"}
                    </span>
                    <button
                        data-testid="editor-save-btn"
                        onClick={onSave}
                        className="flex items-center gap-1.5 px-3 sm:px-4 py-2 text-xs text-ink-faded border hairline border-[rgba(26,25,24,0.18)] hover:border-ink hover:text-ink transition-colors duration-500"
                    >
                        <Save size={13} strokeWidth={1.25} /> Save
                    </button>
                </div>
            </div>
        </header>
    );
}
