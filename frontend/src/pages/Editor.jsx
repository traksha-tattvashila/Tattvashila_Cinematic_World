import React, { useCallback, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { fileUrl } from "../lib/api";
import useEditorState from "../hooks/useEditorState";

import EditorHeader from "../components/editor/EditorHeader";
import EditorPreview from "../components/editor/EditorPreview";
import MediaLibrary from "../components/editor/MediaLibrary";
import Timeline from "../components/editor/Timeline";
import NarrationPanel from "../components/editor/NarrationPanel";
import AmbiencePanel from "../components/editor/AmbiencePanel";
import GradingPanel from "../components/editor/GradingPanel";
import RenderPanel from "../components/editor/RenderPanel";
import RetrievalDialog from "../components/editor/RetrievalDialog";
import Onboarding from "../components/Onboarding";

const TABS = [
    { id: "narration", label: "Narration" },
    { id: "ambience", label: "Ambience" },
    { id: "grading", label: "Grading" },
    { id: "render", label: "Render" },
];

export default function Editor() {
    const { id } = useParams();
    const {
        project, assets, presets, voices,
        loading, saving, dirty,
        update, save,
        refreshAssets, addAsset, removeAsset,
        recoveryOffered, restoreLocalDraft, discardLocalDraft,
    } = useEditorState(id);

    const [tab, setTab] = useState("narration");
    const [retrievalOpen, setRetrievalOpen] = useState(false);

    const onPickClip = useCallback((asset) => {
        if (!project) return;
        const dur = Math.min(8, asset.duration || 8);
        const seg = {
            id: crypto.randomUUID(),
            kind: "clip",
            asset_id: asset.id,
            duration: dur,
            start_offset: 0,
            transition_in: project.segments.length === 0 ? "fade" : "crossfade",
            transition_in_duration: 1.5,
        };
        update({ ...project, segments: [...project.segments, seg] });
    }, [project, update]);

    const onPickAmbientPreset = useCallback((preset) => {
        if (!project) return;
        update({
            ...project,
            ambient: { ...project.ambient, source: "builtin", builtin_key: preset.key },
        });
        setTab("ambience");
    }, [project, update]);

    const onTitleChange = useCallback(
        (next) => project && update({ ...project, title: next }),
        [project, update],
    );

    const heroPreviewUrl = useMemo(() => {
        if (!project) return null;
        const firstClip = project.segments?.find((s) => s.kind === "clip");
        if (!firstClip) return null;
        const a = assets.find((x) => x.id === firstClip.asset_id);
        return a ? fileUrl(a.storage_path) : null;
    }, [project, assets]);

    if (loading || !project) {
        return (
            <div className="min-h-screen bg-paper flex items-center justify-center">
                <p className="text-ink-muted text-sm" data-testid="editor-loading">
                    Composing the workshop…
                </p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-paper text-ink flex flex-col">
            <EditorHeader
                title={project.title}
                subtitle={project.subtitle}
                saving={saving}
                dirty={dirty}
                onTitleChange={onTitleChange}
                onSave={save}
                onOpenRetrieval={() => setRetrievalOpen(true)}
            />

            {recoveryOffered && (
                <div
                    data-testid="recovery-banner"
                    className="border-b hairline border-b-[rgba(26,25,24,0.12)] bg-paper-50 px-4 sm:px-10 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                    <p className="text-sm text-ink-faded italic">
                        An unsaved draft from a previous session was found in this browser.
                    </p>
                    <div className="flex items-center gap-4 text-xs">
                        <button
                            data-testid="recovery-restore"
                            onClick={restoreLocalDraft}
                            className="px-4 py-1.5 bg-ink text-paper tracking-wider hover:bg-ink-faded transition-colors duration-700"
                        >
                            Restore
                        </button>
                        <button
                            data-testid="recovery-discard"
                            onClick={discardLocalDraft}
                            className="text-ink-muted quiet-link tracking-wider uppercase"
                        >
                            Discard
                        </button>
                    </div>
                </div>
            )}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-px bg-[rgba(26,25,24,0.08)]">
                <div className="lg:col-span-3 bg-paper">
                    <MediaLibrary
                        assets={assets}
                        ambientPresets={presets}
                        onUpload={addAsset}
                        onDelete={removeAsset}
                        onPickClip={onPickClip}
                        onPickAmbientPreset={onPickAmbientPreset}
                    />
                </div>

                <div className="lg:col-span-6 bg-paper flex flex-col">
                    <div className="p-4 sm:p-6 border-b hairline border-b-[rgba(26,25,24,0.12)]">
                        <p className="label-eyebrow mb-3">Preview · first frame</p>
                        <EditorPreview
                            posterUrl={heroPreviewUrl}
                            width={project.render_config.width}
                            height={project.render_config.height}
                            fps={project.render_config.fps}
                        />
                        <p className="text-[11px] text-ink-muted italic mt-3 leading-relaxed">
                            This is a static reference frame. The full film — with grading, narration, and ambience — is composed at render time.
                        </p>
                    </div>
                    <div className="p-4 sm:p-6 flex-1">
                        <Timeline project={project} assets={assets} onChange={update} />
                    </div>
                </div>

                <div className="lg:col-span-3 bg-paper flex flex-col">
                    <div className="border-b hairline border-b-[rgba(26,25,24,0.12)] flex">
                        {TABS.map((t) => (
                            <button
                                key={t.id}
                                data-testid={`tab-${t.id}`}
                                onClick={() => setTab(t.id)}
                                className={`flex-1 py-3 sm:py-4 text-[11px] tracking-widest uppercase transition-colors duration-500 ${
                                    tab === t.id
                                        ? "text-ink border-b border-ink -mb-px"
                                        : "text-ink-muted hover:text-ink"
                                }`}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>
                    <div className="p-5 sm:p-6 flex-1 overflow-y-auto">
                        {tab === "narration" && (
                            <NarrationPanel
                                project={project}
                                voices={voices}
                                assets={assets}
                                onChange={update}
                                onAssetAdded={addAsset}
                            />
                        )}
                        {tab === "ambience" && (
                            <AmbiencePanel
                                project={project}
                                presets={presets}
                                assets={assets}
                                onChange={update}
                            />
                        )}
                        {tab === "grading" && (
                            <GradingPanel project={project} onChange={update} />
                        )}
                        {tab === "render" && (
                            <RenderPanel
                                project={project}
                                onChange={update}
                                assets={assets}
                                onAssetAdded={addAsset}
                                onRenderComplete={refreshAssets}
                            />
                        )}
                    </div>
                </div>
            </div>

            <RetrievalDialog
                open={retrievalOpen}
                project={project}
                onClose={() => setRetrievalOpen(false)}
                onAssembled={(updatedProject) => {
                    update(updatedProject);
                    refreshAssets();
                }}
            />

            <Onboarding />
        </div>
    );
}
