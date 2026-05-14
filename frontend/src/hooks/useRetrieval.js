import { useCallback, useState } from "react";
import { http, endpoints } from "../lib/api";
import { logError, niceMessage } from "../lib/log";
import { toast } from "sonner";

const PHASES = {
    IDLE: "idle",
    ANALYZING: "analyzing",
    SEARCHED: "searched",
    ASSEMBLING: "assembling",
};

/**
 * Atmospheric Retrieval state machine.
 *
 * Holds rubric, ranked clips, selection set with per-clip trim overrides,
 * phase, and any provider/threshold suggestions returned by the backend.
 */
export default function useRetrieval({ projectId, onAssembled } = {}) {
    const [rubric, setRubric] = useState(null);
    const [clips, setClips] = useState([]);
    const [selected, setSelected] = useState(() => new Map()); // key -> {trim_start, trim_duration}
    const [phase, setPhase] = useState(PHASES.IDLE);
    const [suggestions, setSuggestions] = useState([]);
    const [reason, setReason] = useState(null);

    const reset = useCallback(() => {
        setRubric(null);
        setClips([]);
        setSelected(new Map());
        setPhase(PHASES.IDLE);
        setSuggestions([]);
        setReason(null);
    }, []);

    const _runSearch = useCallback(
        async ({ description, contemplativeMode, narrationText }) => {
            setPhase(PHASES.ANALYZING);
            setRubric(null);
            setClips([]);
            setSelected(new Map());
            setSuggestions([]);
            setReason(null);
            try {
                const r = await http.post(endpoints.retrievalSearch, {
                    description: description.trim(),
                    contemplative_mode: contemplativeMode,
                    narration_text: narrationText || null,
                    per_query: 4,
                });
                setRubric(r.data.rubric);
                setClips(r.data.clips || []);
                setSuggestions(r.data.suggestions || []);
                setReason(r.data.reason || null);
                setPhase(PHASES.SEARCHED);
                return r.data;
            } catch (e) {
                logError("retrieval search failed", e);
                toast.error(niceMessage(e, "Retrieval failed"));
                setPhase(PHASES.IDLE);
                return null;
            }
        },
        [],
    );

    const search = useCallback(
        ({ description, contemplativeMode, narrationText }) => {
            if (!description?.trim() || phase === PHASES.ANALYZING) return;
            return _runSearch({ description, contemplativeMode, narrationText });
        },
        [phase, _runSearch],
    );

    const widenThreshold = useCallback(
        ({ description, narrationText }) =>
            _runSearch({ description, contemplativeMode: false, narrationText }),
        [_runSearch],
    );

    const toggleSelect = useCallback((clip) => {
        setSelected((prev) => {
            const k = `${clip.provider}|${clip.external_id}`;
            const next = new Map(prev);
            if (next.has(k)) {
                next.delete(k);
            } else {
                // Default trim — let the backend's adaptive_trim run unless user overrides
                next.set(k, { trim_start: null, trim_duration: null });
            }
            return next;
        });
    }, []);

    const setTrim = useCallback((clip, patch) => {
        setSelected((prev) => {
            const k = `${clip.provider}|${clip.external_id}`;
            if (!prev.has(k)) return prev;
            const next = new Map(prev);
            next.set(k, { ...next.get(k), ...patch });
            return next;
        });
    }, []);

    const getTrim = useCallback(
        (clip) => selected.get(`${clip.provider}|${clip.external_id}`) || null,
        [selected],
    );

    const isSelected = useCallback(
        (clip) => selected.has(`${clip.provider}|${clip.external_id}`),
        [selected],
    );

    const assemble = useCallback(
        async ({ pacing, transition = "crossfade", atmosphere }) => {
            if (selected.size === 0) {
                toast.error("Select at least one clip");
                return null;
            }
            const selections = clips
                .filter((c) => selected.has(`${c.provider}|${c.external_id}`))
                .map((c) => {
                    const trim = selected.get(`${c.provider}|${c.external_id}`) || {};
                    return {
                        provider: c.provider,
                        external_id: c.external_id,
                        title: c.title || "",
                        tags: c.tags || [],
                        duration: c.duration || 0,
                        width: c.width || 0,
                        height: c.height || 0,
                        download_url: c.download_url,
                        preview_url: c.preview_url || "",
                        thumbnail_url: c.thumbnail_url || "",
                        author: c.author || "",
                        source_url: c.source_url || "",
                        trim_start: trim.trim_start,
                        trim_duration: trim.trim_duration,
                    };
                });
            setPhase(PHASES.ASSEMBLING);
            try {
                const r = await http.post(endpoints.retrievalAssemble, {
                    project_id: projectId,
                    selections,
                    pacing: pacing || "slow",
                    transition,
                    rubric_atmosphere: atmosphere || "",
                    rubric,
                });
                toast.success(
                    `${selections.length} clip${selections.length === 1 ? "" : "s"} woven into the timeline`,
                );
                onAssembled?.(r.data);
                return r.data;
            } catch (e) {
                logError("retrieval assemble failed", e);
                toast.error(niceMessage(e, "Assembly failed"));
                setPhase(PHASES.SEARCHED);
                return null;
            }
        },
        [clips, selected, projectId, onAssembled, rubric],
    );

    return {
        phase, rubric, clips, selected, suggestions, reason,
        search, widenThreshold, toggleSelect, isSelected,
        getTrim, setTrim, assemble, reset,
        PHASES,
    };
}
