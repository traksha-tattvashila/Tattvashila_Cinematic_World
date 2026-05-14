import { useCallback, useEffect, useRef, useState } from "react";
import { http, endpoints } from "../lib/api";
import { logError, niceMessage } from "../lib/log";
import { toast } from "sonner";

const POLL_INTERVAL_MS = 2000;
const ACTIVE = new Set(["queued", "rendering"]);
const TERMINAL = new Set(["completed", "failed"]);

/**
 * Tracks render-job lifecycle for a single project.
 *
 * Owns: current job + history. Auto-polls while active.
 * Exposes elapsed time, ETA, last-tick timestamp, and online state so the
 * dedicated render progress view can render contemplative network awareness.
 */
export default function useRenderJob({ projectId, onComplete } = {}) {
    const [job, setJob] = useState(null);
    const [history, setHistory] = useState([]);
    const [elapsedMs, setElapsedMs] = useState(0);
    const [lastTickAt, setLastTickAt] = useState(null);
    const [online, setOnline] = useState(
        typeof navigator !== "undefined" ? navigator.onLine : true,
    );

    const onCompleteRef = useRef(onComplete);
    onCompleteRef.current = onComplete;

    // Network awareness
    useEffect(() => {
        if (typeof window === "undefined") return undefined;
        const up = () => setOnline(true);
        const down = () => setOnline(false);
        window.addEventListener("online", up);
        window.addEventListener("offline", down);
        return () => {
            window.removeEventListener("online", up);
            window.removeEventListener("offline", down);
        };
    }, []);

    const fetchHistory = useCallback(async () => {
        try {
            const r = await http.get(endpoints.projectRenders(projectId));
            setHistory(r.data);
            const active = r.data.find((j) => ACTIVE.has(j.status));
            if (active && (!job || job.id !== active.id)) {
                setJob(active);
            }
        } catch (e) {
            logError("render history fetch failed", e);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [projectId]);

    useEffect(() => {
        if (projectId) fetchHistory();
    }, [projectId, fetchHistory]);

    // Compute elapsed time: prefer backend `started_at` if present, else
    // fall back to the moment the job entered the hook.
    const startBaseRef = useRef(null);
    useEffect(() => {
        if (!job) {
            startBaseRef.current = null;
            setElapsedMs(0);
            return undefined;
        }
        if (TERMINAL.has(job.status)) {
            // Freeze elapsed at completed_at - started_at, if available
            if (job.started_at && job.completed_at) {
                const dt = new Date(job.completed_at) - new Date(job.started_at);
                if (!Number.isNaN(dt) && dt >= 0) setElapsedMs(dt);
            }
            return undefined;
        }
        const baseMs = job.started_at
            ? new Date(job.started_at).getTime()
            : Date.now();
        startBaseRef.current = baseMs;
        const id = setInterval(() => {
            setElapsedMs(Math.max(0, Date.now() - baseMs));
        }, 500);
        return () => clearInterval(id);
    }, [job]);

    // Polling for an active job
    useEffect(() => {
        if (!job || TERMINAL.has(job.status)) return undefined;
        let cancelled = false;
        const id = setInterval(async () => {
            try {
                const r = await http.get(endpoints.renderJob(job.id));
                if (cancelled) return;
                setJob(r.data);
                setLastTickAt(Date.now());
                if (TERMINAL.has(r.data.status)) {
                    fetchHistory();
                    if (r.data.status === "completed") {
                        onCompleteRef.current?.(r.data);
                    }
                }
            } catch (e) {
                logError("render poll failed", e);
            }
        }, POLL_INTERVAL_MS);
        return () => { cancelled = true; clearInterval(id); };
    }, [job, fetchHistory]);

    const start = useCallback(async () => {
        try {
            const r = await http.post(endpoints.renderProject(projectId));
            setJob(r.data);
            toast.success("Render begun. Take a breath — slow cinema takes time.");
            return r.data;
        } catch (e) {
            logError("render start failed", e);
            toast.error(niceMessage(e, "Could not start render"));
            return null;
        }
    }, [projectId]);

    // Estimated time remaining (ms): naive — current elapsed scaled by
    // remaining progress fraction. Returns null until we have meaningful data.
    let etaMs = null;
    if (
        job &&
        !TERMINAL.has(job.status) &&
        job.progress > 0.05 &&
        job.progress < 1.0 &&
        elapsedMs > 2000
    ) {
        const fracRemaining = Math.max(0, 1 - job.progress);
        etaMs = (elapsedMs / Math.max(0.001, job.progress)) * fracRemaining;
    }

    return {
        job,
        history,
        start,
        elapsedMs,
        etaMs,
        lastTickAt,
        online,
    };
}
