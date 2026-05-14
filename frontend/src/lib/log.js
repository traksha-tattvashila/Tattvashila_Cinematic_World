// Production-aware logger.
// In dev (NODE_ENV !== 'production') it forwards to the console.
// In prod it is silent — preserves user-facing UX without leaking errors.
const isProd = process.env.NODE_ENV === "production";

export const logError = (...args) => {
    if (!isProd && typeof console !== "undefined") {
        // eslint-disable-next-line no-console
        console.error(...args);
    }
};

export const logWarn = (...args) => {
    if (!isProd && typeof console !== "undefined") {
        // eslint-disable-next-line no-console
        console.warn(...args);
    }
};

// Extract a human-friendly error message from an Axios / fetch error.
export const niceMessage = (err, fallback = "Something went wrong.") => {
    if (!err) return fallback;
    return (
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        fallback
    );
};
