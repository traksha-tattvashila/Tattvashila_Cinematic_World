import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { http, endpoints } from "../lib/api";
import { logError, niceMessage } from "../lib/log";
import { toast } from "sonner";

const AUTOSAVE_DEBOUNCE_MS = 1500;
const LOCAL_KEY = (id) => `tattva.draft.${id}`;
const LOCAL_TTL_MS = 1000 * 60 * 60 * 24 * 7; // 7 days

/**
 * Editor-page state hook.
 *
 * Owns: project, assets, presets, voices, dirty/saving flags.
 * Robust against navigation / browser-close: every dirty change is mirrored
 * to localStorage. On reload, if the local copy is newer than the server's
 * `updated_at`, the user is offered the option to restore.
 */
export default function useEditorState(projectId) {
    const navigate = useNavigate();
    const [project, setProject] = useState(null);
    const [assets, setAssets] = useState([]);
    const [presets, setPresets] = useState([]);
    const [voices, setVoices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [dirty, setDirty] = useState(false);
    const [recoveryOffered, setRecoveryOffered] = useState(false);

    const projectRef = useRef(null);
    projectRef.current = project;

    // Initial load — once per project id
    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const [proj, mediaRes, ambRes, voiceRes] = await Promise.all([
                    http.get(endpoints.project(projectId)),
                    http.get(endpoints.media),
                    http.get(endpoints.ambientLibrary),
                    http.get(endpoints.narrationVoices),
                ]);
                if (cancelled) return;

                // Check for a newer local draft
                const local = readLocalDraft(projectId);
                if (local && new Date(local.savedAt) > new Date(proj.data.updated_at)) {
                    setRecoveryOffered(true);
                }
                setProject(proj.data);
                setAssets(mediaRes.data);
                setPresets(ambRes.data.presets);
                setVoices(voiceRes.data.voices);
            } catch (e) {
                logError("editor load failed", e);
                toast.error(niceMessage(e, "Could not load this work"));
                navigate("/projects");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [projectId, navigate]);

    const update = useCallback((next) => {
        setProject(next);
        setDirty(true);
        writeLocalDraft(projectId, next);
    }, [projectId]);

    const save = useCallback(async () => {
        const p = projectRef.current;
        if (!p) return;
        setSaving(true);
        try {
            const payload = {
                title: p.title,
                subtitle: p.subtitle,
                description: p.description,
                segments: p.segments,
                narration: p.narration,
                ambient: p.ambient,
                grading: p.grading,
                render_config: p.render_config,
            };
            const r = await http.patch(endpoints.project(p.id), payload);
            setProject(r.data);
            setDirty(false);
            clearLocalDraft(projectId);
        } catch (e) {
            logError("save failed", e);
            toast.error(niceMessage(e, "Save failed — your local draft is preserved"));
        } finally {
            setSaving(false);
        }
    }, [projectId]);

    // Debounced auto-save
    useEffect(() => {
        if (!dirty) return undefined;
        const t = setTimeout(save, AUTOSAVE_DEBOUNCE_MS);
        return () => clearTimeout(t);
    }, [dirty, project, save]);

    const refreshAssets = useCallback(async () => {
        try {
            const m = await http.get(endpoints.media);
            setAssets(m.data);
        } catch (e) {
            logError("media refresh failed", e);
        }
    }, []);

    const addAsset = useCallback((asset) => {
        setAssets((xs) => [asset, ...xs.filter((x) => x.id !== asset.id)]);
    }, []);

    const removeAsset = useCallback(async (asset) => {
        try {
            await http.delete(endpoints.mediaDelete(asset.id));
            setAssets((xs) => xs.filter((x) => x.id !== asset.id));
            toast.success("Removed.");
        } catch (e) {
            logError("delete asset failed", e);
            toast.error(niceMessage(e, "Could not remove"));
        }
    }, []);

    const restoreLocalDraft = useCallback(() => {
        const local = readLocalDraft(projectId);
        if (!local) return;
        setProject(local.project);
        setDirty(true);
        setRecoveryOffered(false);
        toast.success("Local draft restored.");
    }, [projectId]);

    const discardLocalDraft = useCallback(() => {
        clearLocalDraft(projectId);
        setRecoveryOffered(false);
    }, [projectId]);

    return {
        project, assets, presets, voices,
        loading, saving, dirty,
        update, save,
        setProject, refreshAssets, addAsset, removeAsset,
        recoveryOffered, restoreLocalDraft, discardLocalDraft,
    };
}

// ---------------------------------------------------------------------------
// LocalStorage draft helpers (browser-only, gracefully ignored on SSR)
// ---------------------------------------------------------------------------
function readLocalDraft(projectId) {
    try {
        const raw = window?.localStorage?.getItem(LOCAL_KEY(projectId));
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        if (!parsed?.savedAt) return null;
        if (Date.now() - new Date(parsed.savedAt).getTime() > LOCAL_TTL_MS) {
            window.localStorage.removeItem(LOCAL_KEY(projectId));
            return null;
        }
        return parsed;
    } catch {
        return null;
    }
}

function writeLocalDraft(projectId, project) {
    try {
        window?.localStorage?.setItem(
            LOCAL_KEY(projectId),
            JSON.stringify({ savedAt: new Date().toISOString(), project }),
        );
    } catch {
        /* quota exceeded or private mode — silently ignore */
    }
}

function clearLocalDraft(projectId) {
    try {
        window?.localStorage?.removeItem(LOCAL_KEY(projectId));
    } catch {
        /* ignore */
    }
}
