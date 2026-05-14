import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { http, endpoints } from "../lib/api";
import { logError, niceMessage } from "../lib/log";
import Layout from "../components/Layout";
import { toast } from "sonner";

export default function Projects() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [form, setForm] = useState({ title: "", subtitle: "", description: "" });
    const [showForm, setShowForm] = useState(false);
    const navigate = useNavigate();

    const fetchProjects = async () => {
        try {
            const r = await http.get(endpoints.projects);
            setProjects(r.data);
        } catch (e) {
            logError("projects load failed", e);
            toast.error("Could not load works");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchProjects(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!form.title.trim()) return toast.error("A title is required");
        setCreating(true);
        try {
            const r = await http.post(endpoints.projects, form);
            navigate(`/editor/${r.data.id}`);
        } catch (e) {
            logError("project create failed", e);
            toast.error(niceMessage(e, "Could not create the work"));
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Withdraw this work? The act is permanent.")) return;
        try {
            await http.delete(endpoints.project(id));
            setProjects((p) => p.filter((x) => x.id !== id));
            toast.success("Withdrawn.");
        } catch (e) {
            logError("project delete failed", e);
            toast.error("Could not withdraw.");
        }
    };

    return (
        <Layout>
            <div className="grid grid-cols-12 gap-6 items-end mb-16">
                <div className="col-span-12 md:col-span-7">
                    <p className="label-eyebrow mb-6">The catalogue</p>
                    <h1
                        className="font-serif text-5xl md:text-6xl text-ink leading-tight"
                        data-testid="projects-title"
                    >
                        Works in progress.
                    </h1>
                </div>
                <div className="col-span-12 md:col-span-5 flex md:justify-end">
                    <button
                        data-testid="new-project-btn"
                        onClick={() => setShowForm((s) => !s)}
                        className="inline-flex items-center px-6 py-3 bg-ink text-paper text-sm tracking-wide hover:bg-ink-faded transition-colors duration-700 ease-in-out"
                    >
                        {showForm ? "Close" : "Begin a new work"}
                    </button>
                </div>
            </div>

            {showForm && (
                <form
                    onSubmit={handleCreate}
                    data-testid="new-project-form"
                    className="border hairline border-[rgba(26,25,24,0.15)] p-10 mb-16 animate-fade-in bg-paper-50"
                >
                    <div className="grid grid-cols-12 gap-8">
                        <div className="col-span-12 md:col-span-6">
                            <label className="label-eyebrow block mb-3">Title</label>
                            <input
                                data-testid="project-title-input"
                                value={form.title}
                                onChange={(e) => setForm({ ...form, title: e.target.value })}
                                placeholder="e.g., The Quiet Civilisation"
                                className="w-full bg-transparent border-0 border-b border-[rgba(26,25,24,0.25)] focus:border-ink outline-none py-3 font-serif text-2xl text-ink placeholder:text-ink-soft transition-colors duration-500"
                            />
                        </div>
                        <div className="col-span-12 md:col-span-6">
                            <label className="label-eyebrow block mb-3">Subtitle</label>
                            <input
                                data-testid="project-subtitle-input"
                                value={form.subtitle}
                                onChange={(e) => setForm({ ...form, subtitle: e.target.value })}
                                placeholder="A meditation on modernity"
                                className="w-full bg-transparent border-0 border-b border-[rgba(26,25,24,0.25)] focus:border-ink outline-none py-3 text-base text-ink placeholder:text-ink-soft transition-colors duration-500"
                            />
                        </div>
                        <div className="col-span-12">
                            <label className="label-eyebrow block mb-3">Intention</label>
                            <textarea
                                data-testid="project-description-input"
                                value={form.description}
                                onChange={(e) => setForm({ ...form, description: e.target.value })}
                                rows={3}
                                placeholder="What is this film attempting to hold?"
                                className="w-full bg-transparent border border-[rgba(26,25,24,0.18)] focus:border-ink outline-none p-4 text-sm text-ink-faded placeholder:text-ink-soft transition-colors duration-500 resize-none"
                            />
                        </div>
                    </div>
                    <div className="mt-8 flex justify-end gap-4">
                        <button
                            type="button"
                            data-testid="cancel-create-btn"
                            onClick={() => setShowForm(false)}
                            className="px-5 py-2 text-sm text-ink-faded quiet-link"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={creating}
                            data-testid="submit-create-btn"
                            className="px-6 py-3 bg-ink text-paper text-sm tracking-wide hover:bg-ink-faded transition-colors duration-700 ease-in-out disabled:opacity-50"
                        >
                            {creating ? "Inscribing…" : "Open the timeline →"}
                        </button>
                    </div>
                </form>
            )}

            {loading ? (
                <p className="text-ink-muted text-sm" data-testid="projects-loading">
                    Loading the catalogue…
                </p>
            ) : projects.length === 0 ? (
                <div
                    className="border hairline border-[rgba(26,25,24,0.15)] p-16 text-center"
                    data-testid="projects-empty"
                >
                    <p className="font-serif text-2xl text-ink-faded italic mb-2">
                        The catalogue is still.
                    </p>
                    <p className="text-sm text-ink-muted">
                        Begin a work to break the silence.
                    </p>
                </div>
            ) : (
                <div className="border-t hairline border-t-[rgba(26,25,24,0.12)]">
                    {projects.map((p, i) => (
                        <div
                            key={p.id}
                            data-testid={`project-row-${p.id}`}
                            className="grid grid-cols-12 gap-6 py-10 border-b hairline border-b-[rgba(26,25,24,0.12)] group items-baseline"
                        >
                            <span className="col-span-2 md:col-span-1 font-mono text-xs text-ink-muted">
                                {String(i + 1).padStart(2, "0")}
                            </span>
                            <Link
                                to={`/editor/${p.id}`}
                                className="col-span-10 md:col-span-6 block"
                            >
                                <h3 className="font-serif text-3xl text-ink group-hover:text-ink-faded transition-colors duration-500">
                                    {p.title}
                                </h3>
                                {p.subtitle && (
                                    <p className="text-sm text-ink-muted mt-1 italic">
                                        {p.subtitle}
                                    </p>
                                )}
                            </Link>
                            <span className="col-span-6 md:col-span-3 text-xs font-mono text-ink-muted tracking-wider">
                                {(p.segments?.length || 0)} SEGMENTS ·{" "}
                                {new Date(p.updated_at).toLocaleDateString(undefined, {
                                    year: "numeric",
                                    month: "short",
                                    day: "numeric",
                                })}
                            </span>
                            <div className="col-span-6 md:col-span-2 flex md:justify-end gap-4 text-sm">
                                <Link
                                    to={`/editor/${p.id}`}
                                    data-testid={`open-project-${p.id}`}
                                    className="quiet-link text-ink-faded"
                                >
                                    Open
                                </Link>
                                <button
                                    data-testid={`delete-project-${p.id}`}
                                    onClick={() => handleDelete(p.id)}
                                    className="quiet-link text-ink-muted hover:text-destructive"
                                >
                                    Withdraw
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </Layout>
    );
}
