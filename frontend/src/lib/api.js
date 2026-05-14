import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const http = axios.create({
    baseURL: API,
    timeout: 600000,
});

export const fileUrl = (storagePath) => `${API}/files/${storagePath}`;

export const endpoints = {
    health: "/health",
    projects: "/projects",
    project: (id) => `/projects/${id}`,
    renderProject: (id) => `/projects/${id}/render`,
    renderJob: (id) => `/render/${id}`,
    renderProvenance: (id) => `/render/${id}/provenance`,
    projectRenders: (id) => `/projects/${id}/renders`,
    media: "/media",
    mediaUpload: "/media/upload",
    mediaDelete: (id) => `/media/${id}`,
    ambientLibrary: "/ambient/library",
    ambientPreview: (key) => `/ambient/preview/${key}`,
    narrationVoices: "/narration/voices",
    narrationTTS: "/narration/tts",
    retrievalAnalyze: "/retrieval/analyze",
    retrievalSearch: "/retrieval/search",
    retrievalAssemble: "/retrieval/assemble",
};

export const fullUrl = (endpoint) => `${API}${endpoint}`;
