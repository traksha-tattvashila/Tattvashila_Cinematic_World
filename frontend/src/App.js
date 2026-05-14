import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";

import Landing from "@/pages/Landing";
import Projects from "@/pages/Projects";
import Editor from "@/pages/Editor";
import ErrorBoundary from "@/components/ErrorBoundary";

function App() {
    return (
        <div className="App">
            <ErrorBoundary>
                <BrowserRouter>
                    <Toaster
                        position="bottom-right"
                        toastOptions={{
                            style: {
                                background: "#1A1918",
                                color: "#F4F0EB",
                                border: "1px solid rgba(244,240,235,0.2)",
                                borderRadius: 0,
                                fontFamily: "IBM Plex Sans, sans-serif",
                                fontSize: "13px",
                            },
                        }}
                    />
                    <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route path="/projects" element={<Projects />} />
                        <Route path="/editor/:id" element={<Editor />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </BrowserRouter>
            </ErrorBoundary>
        </div>
    );
}

export default App;
