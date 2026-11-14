"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ApiClientError,
  apiErrorMessage,
  createProject,
  getSession,
  listJobs,
  listModels,
  listProjects,
  login,
  logout,
  submitImageJob,
  submitTextJob,
} from "@/lib/api";
import type { Job, Project } from "@/lib/contracts";
import {
  jobStatusDescription,
  jobStatusLabel,
  needsOperatorAttention,
  statusTone,
} from "@/lib/status";
import { ModelViewer } from "./model-viewer";

type AuthState = "checking" | "anonymous" | "authenticated";
type GenerationMode = "text" | "image";

function shortId(value: string): string {
  return value.length > 14 ? `${value.slice(0, 7)}…${value.slice(-5)}` : value;
}

function when(value: number): string {
  return new Date(value * 1000).toLocaleString();
}

export function Studio() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectFromUrl = searchParams.get("project");

  const [auth, setAuth] = useState<AuthState>("checking");
  const [userId, setUserId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [modelId, setModelId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [generationMode, setGenerationMode] = useState<GenerationMode>("text");
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [projectName, setProjectName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const report = useCallback((cause: unknown) => {
    setError(apiErrorMessage(cause));
  }, []);

  const loadWorkspace = useCallback(
    async (preferredProject?: string | null) => {
      const [availableModels, availableProjects] = await Promise.all([
        listModels(),
        listProjects(),
      ]);
      setModels(availableModels);
      setModelId((current) =>
        availableModels.includes(current) ? current : (availableModels[0] ?? ""),
      );
      setProjects(availableProjects);

      const preferred = preferredProject ?? selectedProjectId;
      const nextProject =
        (preferred && availableProjects.some((item) => item.id === preferred)
          ? preferred
          : availableProjects[0]?.id) ?? null;
      setSelectedProjectId(nextProject);
      if (nextProject) {
        router.replace(`/?project=${encodeURIComponent(nextProject)}`);
      } else {
        router.replace("/");
      }
    },
    [router, selectedProjectId],
  );

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const session = await getSession();
        if (!active) return;
        setUserId(session.userId);
        setAuth("authenticated");
        await loadWorkspace(projectFromUrl);
      } catch (cause) {
        if (!active) return;
        if (cause instanceof ApiClientError && cause.status === 401) {
          setAuth("anonymous");
        } else {
          setAuth("anonymous");
          report(cause);
        }
      }
    })();
    return () => {
      active = false;
    };
    // Initial session check intentionally runs once; projectFromUrl is used as the initial preference.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshJobs = useCallback(
    async (projectId: string, signal?: AbortSignal) => {
      const latest = await listJobs(projectId, signal);
      setJobs(latest);
      setSelectedJobId((current) =>
        current && latest.some((job) => job.id === current)
          ? current
          : (latest[0]?.id ?? null),
      );
    },
    [],
  );

  useEffect(() => {
    if (auth !== "authenticated" || !selectedProjectId) {
      setJobs([]);
      setSelectedJobId(null);
      return;
    }
    let controller = new AbortController();
    const run = async () => {
      try {
        await refreshJobs(selectedProjectId, controller.signal);
      } catch (cause) {
        if (!controller.signal.aborted) report(cause);
      }
    };
    void run();
    const timer = window.setInterval(() => {
      controller.abort();
      controller = new AbortController();
      void run();
    }, 5000);
    return () => {
      window.clearInterval(timer);
      controller.abort();
    };
  }, [auth, refreshJobs, report, selectedProjectId]);

  const selectedProject = useMemo(
    () => projects.find((item) => item.id === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );
  const selectedJob = useMemo(
    () => jobs.find((item) => item.id === selectedJobId) ?? null,
    [jobs, selectedJobId],
  );

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const session = await login(apiKey);
      setApiKey("");
      setUserId(session.userId);
      setAuth("authenticated");
      await loadWorkspace(projectFromUrl);
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    setBusy(true);
    try {
      await logout();
    } catch {
      // Session is cleared locally even if the backend is unavailable.
    }
    setAuth("anonymous");
    setUserId("");
    setProjects([]);
    setModels([]);
    setJobs([]);
    setSelectedProjectId(null);
    setSelectedJobId(null);
    router.replace("/");
    setBusy(false);
  }

  async function handleCreateProject(event: FormEvent) {
    event.preventDefault();
    if (!projectName.trim()) return;
    setBusy(true);
    setError("");
    try {
      const created = await createProject(projectName.trim());
      setProjectName("");
      setProjects((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setSelectedProjectId(created.id);
      setSelectedJobId(null);
      router.replace(`/?project=${encodeURIComponent(created.id)}`);
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
    }
  }

  async function handleTextGeneration(event: FormEvent) {
    event.preventDefault();
    if (!selectedProjectId || !modelId || !prompt.trim()) return;
    setBusy(true);
    setError("");
    try {
      const job = await submitTextJob(selectedProjectId, prompt.trim(), modelId);
      setPrompt("");
      setSelectedJobId(job.id);
      await refreshJobs(selectedProjectId);
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
    }
  }

  async function handleImageGeneration(event: FormEvent) {
    event.preventDefault();
    if (!selectedProjectId || !modelId || !image) return;
    setBusy(true);
    setError("");
    try {
      const job = await submitImageJob(selectedProjectId, image, modelId);
      setImage(null);
      setSelectedJobId(job.id);
      await refreshJobs(selectedProjectId);
      const input = document.getElementById("reference-image") as HTMLInputElement | null;
      if (input) input.value = "";
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
    }
  }

  function chooseProject(projectId: string) {
    setSelectedProjectId(projectId);
    setSelectedJobId(null);
    router.replace(`/?project=${encodeURIComponent(projectId)}`);
  }

  if (auth === "checking") {
    return <div className="center-state">Checking private API session…</div>;
  }

  if (auth === "anonymous") {
    return (
      <div className="login-shell">
        <section className="login-card">
          <div className="brand-mark">B3</div>
          <p className="eyebrow">Private product milestone</p>
          <h1>Build 3D AI Studio</h1>
          <p className="muted">
            Connect with an operator-provisioned user API key. The key is stored in an
            HttpOnly server cookie and is never persisted in browser JavaScript storage.
          </p>
          {error && <div className="alert error-alert">{error}</div>}
          <form onSubmit={handleLogin} className="stack-form">
            <label htmlFor="api-key">User API key</label>
            <input
              id="api-key"
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="b3d_…"
              minLength={24}
              required
            />
            <button className="primary-button" disabled={busy}>
              {busy ? "Connecting…" : "Connect to product API"}
            </button>
          </form>
          <p className="security-note">
            This is not public signup. Operator and upstream GPU credentials must never be entered here.
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="app-frame">
      <header className="topbar">
        <div>
          <strong>Build 3D AI</strong>
          <span className="product-pill">Private Studio</span>
        </div>
        <div className="topbar-actions">
          <span className="user-chip" title={userId}>User {shortId(userId)}</span>
          <button className="secondary-button compact" onClick={handleLogout} disabled={busy}>
            Sign out
          </button>
        </div>
      </header>

      {error && (
        <div className="global-alert">
          <span>{error}</span>
          <button aria-label="Dismiss error" onClick={() => setError("")}>×</button>
        </div>
      )}

      <div className="studio-grid">
        <aside className="panel project-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Workspace</p>
              <h2>Projects</h2>
            </div>
            <span className="count-badge">{projects.length}</span>
          </div>
          <form onSubmit={handleCreateProject} className="mini-form">
            <label htmlFor="project-name">New project</label>
            <div className="inline-form">
              <input
                id="project-name"
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
                placeholder="Character assets"
                maxLength={120}
                required
              />
              <button className="primary-button compact" disabled={busy}>Add</button>
            </div>
          </form>
          <div className="project-list" aria-label="Project list">
            {projects.length === 0 && (
              <div className="empty-card">Create your first private project to submit work.</div>
            )}
            {projects.map((project) => (
              <button
                key={project.id}
                className={`project-item ${project.id === selectedProjectId ? "selected" : ""}`}
                onClick={() => chooseProject(project.id)}
                data-project-id={project.id}
              >
                <strong>{project.name}</strong>
                <span>{shortId(project.id)}</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="main-column">
          <section className="panel generation-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Generate</p>
                <h2>{selectedProject?.name ?? "Select a project"}</h2>
              </div>
              {models.length > 0 && <span className="count-badge">{models.length} model{models.length === 1 ? "" : "s"}</span>}
            </div>

            {models.length === 0 ? (
              <div className="alert warning-alert" data-testid="no-models">
                <strong>No approved models are configured.</strong>
                <span>
                  Generation is intentionally disabled until an exact model/checkpoint has passed the deployment approval gate.
                </span>
              </div>
            ) : (
              <>
                <div className="mode-tabs" role="tablist" aria-label="Generation input">
                  <button
                    role="tab"
                    aria-selected={generationMode === "text"}
                    className={generationMode === "text" ? "active" : ""}
                    onClick={() => setGenerationMode("text")}
                  >
                    Text → 3D
                  </button>
                  <button
                    role="tab"
                    aria-selected={generationMode === "image"}
                    className={generationMode === "image" ? "active" : ""}
                    onClick={() => setGenerationMode("image")}
                  >
                    Image → 3D
                  </button>
                </div>
                <label htmlFor="model-id">Approved model</label>
                <select id="model-id" value={modelId} onChange={(event) => setModelId(event.target.value)}>
                  {models.map((model) => <option key={model} value={model}>{model}</option>)}
                </select>

                {generationMode === "text" ? (
                  <form className="stack-form" onSubmit={handleTextGeneration}>
                    <label htmlFor="prompt">Prompt</label>
                    <textarea
                      id="prompt"
                      value={prompt}
                      onChange={(event) => setPrompt(event.target.value)}
                      placeholder="A production-ready stylized wooden chair"
                      minLength={1}
                      maxLength={2000}
                      required
                    />
                    <button className="primary-button" disabled={busy || !selectedProjectId || !prompt.trim()}>
                      {busy ? "Submitting…" : "Generate 3D"}
                    </button>
                  </form>
                ) : (
                  <form className="stack-form" onSubmit={handleImageGeneration}>
                    <label htmlFor="reference-image">Reference image</label>
                    <input
                      id="reference-image"
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      onChange={(event) => setImage(event.target.files?.[0] ?? null)}
                      required
                    />
                    <button className="primary-button" disabled={busy || !selectedProjectId || !image}>
                      {busy ? "Uploading…" : "Generate from image"}
                    </button>
                  </form>
                )}
              </>
            )}
          </section>

          <section className="panel viewer-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">Artifact</p>
                <h2>Verified GLB viewer</h2>
              </div>
              {selectedJob?.status === "completed" && (
                <a
                  className="secondary-button compact link-button"
                  href={`/api/product/v1/jobs/${encodeURIComponent(selectedJob.id)}/download`}
                >
                  Download GLB
                </a>
              )}
            </div>
            {!selectedJob && (
              <div className="viewer-placeholder">Select a job to inspect its real persisted state.</div>
            )}
            {selectedJob && selectedJob.status === "completed" && (
              <ModelViewer jobId={selectedJob.id} />
            )}
            {selectedJob && selectedJob.status !== "completed" && (
              <div className="viewer-placeholder status-detail">
                <span className={`status-chip tone-${statusTone(selectedJob.status)}`}>
                  {jobStatusLabel(selectedJob.status)}
                </span>
                <p>{jobStatusDescription(selectedJob.status)}</p>
                {selectedJob.error_code && <code>Error: {selectedJob.error_code}</code>}
                {needsOperatorAttention(selectedJob.status) && (
                  <strong>Do not blindly resubmit this job. Operator reconciliation may be required.</strong>
                )}
              </div>
            )}
          </section>
        </section>

        <aside className="panel jobs-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Persisted history</p>
              <h2>Jobs</h2>
            </div>
            <span className="count-badge">{jobs.length}</span>
          </div>
          <div className="job-list">
            {!selectedProjectId && <div className="empty-card">Select or create a project.</div>}
            {selectedProjectId && jobs.length === 0 && <div className="empty-card">No jobs yet.</div>}
            {jobs.map((job) => (
              <button
                key={job.id}
                onClick={() => setSelectedJobId(job.id)}
                className={`job-card ${selectedJobId === job.id ? "selected" : ""}`}
              >
                <div className="job-card-top">
                  <span className={`status-chip tone-${statusTone(job.status)}`}>{jobStatusLabel(job.status)}</span>
                  <span className="job-kind">{job.kind}</span>
                </div>
                <strong>{job.prompt || (job.kind === "image" ? "Image reference" : "Text generation")}</strong>
                <span>{job.model_id}</span>
                <time>{when(job.created_at)}</time>
                {needsOperatorAttention(job.status) && <span className="attention-note">Operator attention</span>}
              </button>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
