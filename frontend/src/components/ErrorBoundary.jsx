import React from "react";
import { logError } from "../lib/log";

/**
 * Quiet, contemplative error boundary.
 *
 * Falls back to a hand-set apology screen rather than the React red box.
 * Production logs are silenced via logError.
 */
export default class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error, info) {
        logError("ErrorBoundary caught:", error, info);
    }

    reset = () => {
        this.setState({ hasError: false });
    };

    render() {
        if (!this.state.hasError) return this.props.children;

        return (
            <div
                data-testid="error-boundary"
                className="min-h-screen bg-paper text-ink flex items-center justify-center px-8"
            >
                <div className="max-w-xl text-center">
                    <p className="label-eyebrow mb-6">An interruption</p>
                    <h1 className="font-serif text-4xl md:text-5xl text-ink leading-tight mb-6">
                        The workshop fell silent.
                    </h1>
                    <p className="text-base text-ink-faded leading-relaxed mb-10">
                        Something quietly broke. Refresh the page to return to your work — your project is auto-saved.
                    </p>
                    <button
                        onClick={() => window.location.reload()}
                        data-testid="error-reload-btn"
                        className="px-6 py-3 bg-ink text-paper text-sm tracking-wider hover:bg-ink-faded transition-colors duration-700"
                    >
                        Refresh →
                    </button>
                </div>
            </div>
        );
    }
}
