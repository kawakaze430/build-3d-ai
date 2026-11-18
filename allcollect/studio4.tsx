"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ApiClientError,
  apiErrorMessage,
  artifactDownloadUrl,
  createProject,
  getJob,
  getProject,
  getSession,
  getStorageUsage,
  listJobs,
  listModels,
  listProjects,
  login,
  logout,
  submitImageJob,
  submitTextJob,
} from "@/lib/client/api";
import {
  HISTORY_MAX_OFFSET,
  HISTORY_PAGE_SIZE,
  type HistoryPage,
  type Job,
  type Project,
  type StorageUsage,
} from "@/lib/contracts";
import {
  jobStatusDescription,
  jobStatusLabel,
  needsOperatorAttention,
  statusTone,
} from "@/features/jobs/status";
import { ModelViewer } from "@/features/assets/components/model-viewer";

type AuthState = "checking" | "anonymous" | "authenticated";
type GenerationMode = "text" | "image";
type ProjectScope = { id: string };
type JobRefresh = { controller: AbortController; navigating: boolean };

const EMPTY_PAGE = { items: [], offset: 0 };

function jobTitle(job: Job): string {
  return job.prompt || (job.kind === "image" ? "Image reference" : "Text generation");
}

function HistoryControls({
  kind,
  page,
  loading,
  onPage,
}: {
  kind: "project" | "job";
  page: HistoryPage<Project | Job>;
  loading: boolean;
  onPage: (offset: number) => void;
}) {
  const hasNext = page.items.length === HISTORY_PAGE_SIZE && page.offset < HISTORY_MAX_OFFSET;
  if (!page.offset && !hasNext) return null;
  return (
    <nav className="history-controls" aria-label={`${kind} history pages`}>
      <button
        className="secondary-button compact"
        aria-label={`Previous ${kind} page`}
        disabled={loading || page.offset === 0}
        onClick={() => onPage(page.offset - HISTORY_PAGE_SIZE)}
      >
        Previous
      </button>
      <span role="status">{loading ? "Loading…" : `Page ${page.offset / HISTORY_PAGE_SIZE + 1}`}</span>
      <button
        className="secondary-button compact"
        aria-label={`Next ${kind} page`}
        disabled={loading || !hasNext}
        onClick={() => onPage(page.offset + HISTORY_PAGE_SIZE)}
      >
        Next
      </button>
    </nav>
  );
}

function shortId(value: string): string {
  return value.length > 14 ? `${value.slice(0, 7)}…${value.slice(-5)}` : value;
}

function when(value: number): string {
  return new Date(value * 1000).toLocaleString();
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`;
  const units = ["KiB", "MiB", "GiB", "TiB"];
  let scaled = value;
  let unit = -1;
  do {
    scaled /= 1024;
    unit += 1;
  } while (scaled >= 1024 && unit < units.length - 1);
  const digits = scaled >= 10 ? 1 : 2;
  return `${scaled.toFixed(digits).replace(/\.0+$/, "")} ${units[unit]}`;
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
  const [projectPage, setProjectPage] = useState<HistoryPage<Project>>(EMPTY_PAGE);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [storage, setStorage] = useState<StorageUsage | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [jobPage, setJobPage] = useState<HistoryPage<Job>>(EMPTY_PAGE);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [generationMode, setGenerationMode] = useState<GenerationMode>("text");
  const [prompt, setPrompt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [projectName, setProjectName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const workspaceController = useRef<AbortController | null>(null);
  const activeProject = useRef<ProjectScope | null>(null);
  const projectPaging = useRef<{ controller: AbortController; offset: number } | null>(null);
  const activeRefresh = useRef<JobRefresh | null>(null);
  const projectOffset = useRef(0);
  const jobOffset = useRef(0);
  const activeJob = useRef<Job | null>(null);
  const selectedProjectId = selectedProject?.id ?? null;
  const projects = projectPage.items;
  const jobs = jobPage.items;

  const report = useCallback((cause: unknown) => {
    setError(apiErrorMessage(cause));
  }, []);

  const chooseJob = useCallback((job: Job | null) => {
    activeJob.current = job;
    setSelectedJob(job);
  }, []);

  const chooseProject = useCallback((project: Project | null) => {
    const projectId = project?.id ?? null;
    if (projectId !== (activeProject.current?.id ?? null)) {
      activeRefresh.current?.controller.abort();
      activeRefresh.current = null;
      activeProject.current = projectId ? { id: projectId } : null;
      jobOffset.current = 0;
      setJobPage(EMPTY_PAGE);
      setJobsLoading(Boolean(project));
      chooseJob(null);
    }
    setSelectedProject(project);
    router.replace(projectId ? `/?project=${encodeURIComponent(projectId)}` : "/");
  }, [chooseJob, router]);

  const endSession = useCallback((message = "") => {
    workspaceController.current?.abort();
    workspaceController.current = new AbortController();
    activeRefresh.current?.controller.abort();
    activeRefresh.current = null;
    projectPaging.current?.controller.abort();
    projectPaging.current = null;
    projectOffset.current = 0;
    chooseProject(null);
    setAuth("anonymous");
    setUserId("");
    setApiKey("");
    setProjectPage(EMPTY_PAGE);
    setProjectsLoading(false);
    setModels([]);
    setModelId("");
    setStorage(null);
    setGenerationMode("text");
    setPrompt("");
    setImage(null);
    setProjectName("");
    setError(message);
    setBusy(false);
  }, [chooseProject]);

  const reportWorkspaceFailure = useCallback((
    cause: unknown,
    signal: AbortSignal,
    project?: ProjectScope,
  ) => {
    if (signal.aborted) return;
    if (cause instanceof ApiClientError && cause.status === 401) {
      endSession("Your session has ended. Sign in again with a valid user API key.");
    } else if (!project || activeProject.current === project) {
      report(cause);
    }
  }, [endSession, report]);

  const loadWorkspace = useCallback(
    async (preferredProject: string | null, signal: AbortSignal) => {
      const [availableModels, firstPage, usage] = await Promise.all([
        listModels(signal),
        listProjects(0, signal),
        getStorageUsage(signal),
      ]);
      let nextProject = firstPage.items.find((item) => item.id === preferredProject);
      if (!nextProject && preferredProject) {
        try {
          nextProject = await getProject(preferredProject, signal);
        } catch (cause) {
          if (!(cause instanceof ApiClientError && cause.status === 404)) throw cause;
        }
      }
      signal.throwIfAborted();
      setModels(availableModels);
      setModelId((current) =>
        availableModels.includes(current) ? current : (availableModels[0] ?? ""),
      );
      projectOffset.current = 0;
      setProjectPage(firstPage);
      setStorage(usage);
      chooseProject(nextProject ?? firstPage.items[0] ?? null);
    },
    [chooseProject],
  );

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;
    workspaceController.current = controller;
    (async () => {
      try {
        const session = await getSession(signal);
        await loadWorkspace(projectFromUrl, signal);
        if (signal.aborted) return;
        setUserId(session.userId);
        setAuth("authenticated");
      } catch (cause) {
        if (signal.aborted) return;
        if (cause instanceof ApiClientError && cause.status === 401) {
          setAuth("anonymous");
        } else {
          setAuth("anonymous");
          report(cause);
        }
      }
    })();
    return () => {
      workspaceController.current?.abort();
      workspaceController.current = null;
      activeRefresh.current?.controller.abort();
      projectPaging.current?.controller.abort();
      activeProject.current = null;
    };
    // Initial session check intentionally runs once; projectFromUrl is used as the initial preference.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshProjects = useCallback(async (offset: number, workspaceSignal: AbortSignal) => {
    if (workspaceSignal.aborted) return;
    projectPaging.current?.controller.abort();
    const controller = new AbortController();
    const { signal } = controller;
    const request = { controller, offset };
    projectPaging.current = request;
    setProjectsLoading(true);
    try {
      const page = await listProjects(offset, signal);
      if (signal.aborted) return;
      projectOffset.current = offset;
      setProjectPage(page);
    } catch (cause) {
      reportWorkspaceFailure(cause, signal);
    } finally {
      if (projectPaging.current === request && !signal.aborted) {
        projectPaging.current = null;
        setProjectsLoading(false);
      }
    }
  }, [reportWorkspaceFailure]);

  const refreshWorkspace = useCallback(
    async (
      project: ProjectScope | null,
      workspaceSignal: AbortSignal,
      offset: number,
      navigating = false,
    ) => {
      if (workspaceSignal.aborted || activeProject.current !== project) return;
      if (!navigating && activeRefresh.current?.navigating) return;
      activeRefresh.current?.controller.abort();
      const controller = new AbortController();
      const { signal } = controller;
      const refresh = { controller, navigating };
      activeRefresh.current = refresh;
      if (navigating) setJobsLoading(true);
      try {
        const [page, usage] = await Promise.all([
          project ? listJobs(project.id, offset, signal) : Promise.resolve(EMPTY_PAGE),
          navigating ? Promise.resolve(null) : getStorageUsage(signal),
        ]);
        if (signal.aborted || activeProject.current !== project) return;
        jobOffset.current = page.offset;
        setJobPage(page);
        if (usage) setStorage(usage);
        const selected = activeJob.current;
        if (!selected) {
          chooseJob(page.items[0] ?? null);
        } else {
          const visible = page.items.find((job) => job.id === selected.id);
          if (visible) {
            chooseJob(visible);
          } else if (!navigating) {
            const latest = await getJob(selected.id, signal);
            if (!signal.aborted && activeJob.current?.id === selected.id) chooseJob(latest);
          }
        }
      } catch (cause) {
        reportWorkspaceFailure(cause, signal);
      } finally {
        if (!signal.aborted && activeRefresh.current === refresh) {
          activeRefresh.current = null;
          setJobsLoading(false);
        }
      }
    },
    [chooseJob, reportWorkspaceFailure],
  );

  useEffect(() => {
    const project = activeProject.current;
    const signal = workspaceController.current?.signal;
    if (auth !== "authenticated" || !signal || (project?.id ?? null) !== selectedProjectId) return;
    if (project) void refreshWorkspace(project, signal, 0);
    const run = () => void refreshWorkspace(project, signal, jobOffset.current);
    const timer = window.setInterval(run, 5000);
    return () => {
      window.clearInterval(timer);
      activeRefresh.current?.controller.abort();
      activeRefresh.current = null;
    };
  }, [auth, refreshWorkspace, selectedProjectId]);

  function showProjectPage(offset: number) {
    const signal = workspaceController.current?.signal;
    if (!signal) return;
    setError("");
    void refreshProjects(offset, signal);
  }

  function showJobPage(offset: number) {
    const signal = workspaceController.current?.signal;
    const project = activeProject.current;
    if (!signal || !project) return;
    setError("");
    void refreshWorkspace(project, signal, offset, true);
  }

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    const signal = workspaceController.current?.signal;
    if (!signal || signal.aborted) return;
    setBusy(true);
    setError("");
    try {
      const session = await login(apiKey, signal);
      await loadWorkspace(projectFromUrl, signal);
      if (signal.aborted) return;
      setApiKey("");
      setUserId(session.userId);
      setAuth("authenticated");
    } catch (cause) {
      if (!signal.aborted) report(cause);
    } finally {
      if (!signal.aborted) setBusy(false);
    }
  }

  async function handleLogout() {
    const signal = workspaceController.current?.signal;
    if (!signal || signal.aborted) return;
    setBusy(true);
    setError("");
    try {
      await logout(signal);
      if (!signal.aborted) endSession();
    } catch {
      if (!signal.aborted) setError("Could not confirm sign-out. Try again.");
    } finally {
      if (!signal.aborted) setBusy(false);
    }
  }

  async function handleCreateProject(event: FormEvent) {
    event.preventDefault();
    const signal = workspaceController.current?.signal;
    const project = activeProject.current;
    if (!signal || signal.aborted || !projectName.trim()) return;
    setBusy(true);
    setError("");
    try {
      const created = await createProject(projectName.trim(), signal);
      if (signal.aborted) return;
      setProjectName("");
      if (activeProject.current === project) chooseProject(created);
      void refreshProjects(projectPaging.current?.offset ?? projectOffset.current, signal);
    } catch (cause) {
      reportWorkspaceFailure(cause, signal);
    } finally {
      if (!signal.aborted) setBusy(false);
    }
  }

  async function handleTextGeneration(event: FormEvent) {
    event.preventDefault();
    const project = activeProject.current;
    const signal = workspaceController.current?.signal;
    if (!signal || signal.aborted || !project || !modelId || !prompt.trim()) return;
    setBusy(true);
    setError("");
    try {
      const job = await submitTextJob(project.id, prompt.trim(), modelId, signal);
      if (activeProject.current !== project) return;
      setPrompt("");
      chooseJob(job);
      void refreshWorkspace(project, signal, jobOffset.current);
    } catch (cause) {
      reportWorkspaceFailure(cause, signal, project);
    } finally {
      if (!signal.aborted) setBusy(false);
    }
  }

  async function handleImageGeneration(event: FormEvent) {
    event.preventDefault();
    const project = activeProject.current;
    const signal = workspaceController.current?.signal;
    if (!signal || signal.aborted || !project || !modelId || !image) return;
    setBusy(true);
    setError("");
    try {
      const job = await submitImageJob(project.id, image, modelId, signal);
      if (activeProject.current !== project) return;
      setImage(null);
      const input = document.getElementById("reference-image") as HTMLInputElement | null;
      if (input) input.value = "";
      chooseJob(job);
      void refreshWorkspace(project, signal, jobOffset.current);
    } catch (cause) {
      reportWorkspaceFailure(cause, signal, project);
    } finally {
      if (!signal.aborted) setBusy(false);
    }
  }

  const storagePercent = storage
    ? storage.limit_bytes === 0
      ? (storage.used_bytes > 0 ? 100 : 0)
      : Math.min(100, (storage.used_bytes / storage.limit_bytes) * 100)
    : 0;
  const storageNearLimit = storage
    ? storage.over_quota ||
      storage.limit_bytes === 0 ||
      storagePercent >= 80
    : false;

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
            <span className="count-badge" title="Projects on this page">{projects.length}</span>
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
          {storage && (
            <section
              className={`storage-card ${storage.over_quota ? "storage-over" : storageNearLimit ? "storage-near" : ""}`}
              aria-label="Artifact storage"
              data-testid="storage-usage"
            >
              <div className="storage-heading">
                <strong>Storage</strong>
                <span>{Math.round(storagePercent)}%</span>
              </div>
              <div
                className="storage-track"
                role="progressbar"
                aria-label="Artifact storage used"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(storagePercent)}
              >
                <span style={{ width: `${storagePercent}%` }} />
              </div>
              <div className="storage-copy">
                <span>{formatBytes(storage.used_bytes)} of {formatBytes(storage.limit_bytes)}</span>
                <span>{formatBytes(storage.remaining_bytes)} remaining</span>
              </div>
              {storage.over_quota ? (
                <p className="storage-warning">
                  Storage is over quota. New artifacts cannot complete until usage is reduced or the quota is raised.
                </p>
              ) : storageNearLimit ? (
                <p className="storage-warning">
                  Storage is nearing the configured limit. New completed artifacts may fail when the remaining quota is exhausted.
                </p>
              ) : null}
            </section>
          )}
          <HistoryControls kind="project" page={projectPage} loading={projectsLoading} onPage={showProjectPage} />
          <div className="project-list" aria-label="Project list">
            {projects.length === 0 && projectPage.offset === 0 && (
              <div className="empty-card">Create your first private project to submit work.</div>
            )}
            {projects.length === 0 && projectPage.offset > 0 && (
              <div className="empty-card">No projects on this page.</div>
            )}
            {projects.map((project) => (
              <button
                key={project.id}
                className={`project-item ${project.id === selectedProjectId ? "selected" : ""}`}
                onClick={() => chooseProject(project)}
                aria-current={project.id === selectedProjectId || undefined}
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
                  href={artifactDownloadUrl(selectedJob.id)}
                >
                  Download GLB
                </a>
              )}
            </div>
            {!selectedJob && (
              <div className="viewer-placeholder">Select a job to inspect its real persisted state.</div>
            )}
            {selectedJob && <p className="muted job-selection" title={jobTitle(selectedJob)}>{jobTitle(selectedJob)}</p>}
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
            <span className="count-badge" title="Jobs on this page">{jobs.length}</span>
          </div>
          <HistoryControls kind="job" page={jobPage} loading={jobsLoading} onPage={showJobPage} />
          <div className="job-list">
            {!selectedProjectId && <div className="empty-card">Select or create a project.</div>}
            {selectedProjectId && jobs.length === 0 && (
              <div className="empty-card">
                {jobsLoading ? "Loading jobs…" : jobPage.offset ? "No jobs on this page." : "No jobs yet."}
              </div>
            )}
            {jobs.map((job) => (
              <button
                key={job.id}
                onClick={() => chooseJob(job)}
                aria-current={job.id === selectedJob?.id || undefined}
                className={`job-card ${selectedJob?.id === job.id ? "selected" : ""}`}
              >
                <div className="job-card-top">
                  <span className={`status-chip tone-${statusTone(job.status)}`}>{jobStatusLabel(job.status)}</span>
                  <span className="job-kind">{job.kind}</span>
                </div>
                <strong>{jobTitle(job)}</strong>
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
