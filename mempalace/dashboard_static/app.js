(() => {
  const STORAGE_KEY = "mempalace.dashboard.prefs";
  const DEFAULT_BASE = "";

  const state = {
    baseUrl: DEFAULT_BASE,
    token: "",
    miningActive: false,
    ontologyRuns: [],
    selectedOntologyRunId: null,
    selectedArtifactKey: null,
    taxonomy: [],
    drawers: [],
    selectedDrawerId: null,
    selectedScope: { wing: "", room: "" },
    lastSnapshot: null,
    pollTimer: null,
    bootstrapGeneration: 0,
  };

  const el = (id) => document.getElementById(id);

  const ui = {
    apiBase: el("apiBase"),
    tokenInput: el("tokenInput"),
    savePrefs: el("savePrefs"),
    serviceHealth: el("serviceHealth"),
    serviceHealthHint: el("serviceHealthHint"),
    drawerCount: el("drawerCount"),
    drawerCountHint: el("drawerCountHint"),
    embeddingDevice: el("embeddingDevice"),
    embeddingDeviceHint: el("embeddingDeviceHint"),
    miningState: el("miningState"),
    miningStateHint: el("miningStateHint"),
    localaiStatus: el("localaiStatus"),
    checkpointStatus: el("checkpointStatus"),
    lastRefresh: el("lastRefresh"),
    connectionState: el("connectionState"),
    ontologyRunState: el("ontologyRunState"),
    ontologyRunStatus: el("ontologyRunStatus"),
    ontologyRunSummary: el("ontologyRunSummary"),
    ontologyRunList: el("ontologyRunList"),
    ontologyRunTitle: el("ontologyRunTitle"),
    ontologyRunMeta: el("ontologyRunMeta"),
    ontologyProgressBar: el("ontologyProgressBar"),
    ontologyProgressLabel: el("ontologyProgressLabel"),
    ontologyProgressPercent: el("ontologyProgressPercent"),
    ontologyProgressStats: el("ontologyProgressStats"),
    ontologyProgressDetail: el("ontologyProgressDetail"),
    ontologyArtifactSummary: el("ontologyArtifactSummary"),
    ontologyArtifactList: el("ontologyArtifactList"),
    ontologyArtifactDetail: el("ontologyArtifactDetail"),
    ontologyPreviewStatus: el("ontologyPreviewStatus"),
    ontologyPreviewList: el("ontologyPreviewList"),
    searchLock: el("searchLock"),
    searchForm: el("searchForm"),
    searchQuery: el("searchQuery"),
    wingFilter: el("wingFilter"),
    roomFilter: el("roomFilter"),
    searchButton: el("searchButton"),
    searchSummary: el("searchSummary"),
    searchResults: el("searchResults"),
    taxonomyStatus: el("taxonomyStatus"),
    taxonomyGrid: el("taxonomyGrid"),
    drawerScope: el("drawerScope"),
    drawerList: el("drawerList"),
    drawerDetail: el("drawerDetail"),
    detailTitle: el("detailTitle"),
  };

  function loadPrefs() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      if (typeof parsed.baseUrl === "string" && parsed.baseUrl.trim()) {
        state.baseUrl = parsed.baseUrl.trim();
      }
      if (typeof parsed.token === "string") {
        state.token = parsed.token;
      }
    } catch {
      // Ignore corrupt localStorage state.
    }
    ui.apiBase.value = state.baseUrl;
    ui.tokenInput.value = state.token;
  }

  function savePrefs() {
    state.baseUrl = normalizeBase(ui.apiBase.value);
    state.token = ui.tokenInput.value.trim();
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ baseUrl: state.baseUrl, token: state.token }));
    if (state.token) {
      renderConnectionState("Saved");
      return;
    }
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    renderDisconnectedState("Token required to load dashboard data.");
  }

  function normalizeBase(value) {
    const trimmed = String(value || "").trim();
    if (!trimmed) return DEFAULT_BASE;
    return trimmed.replace(/\/+$/, "");
  }

  function joinUrl(base, path) {
    const cleanBase = normalizeBase(base);
    const cleanPath = String(path || "").replace(/^\/+/, "");
    if (!cleanBase) return `/${cleanPath}`;
    return `${cleanBase}/${cleanPath}`;
  }

  function authHeaders(extra = {}) {
    const headers = { ...extra };
    if (state.token) {
      headers.Authorization = `Bearer ${state.token}`;
    }
    return headers;
  }

  function hasToken() {
    return Boolean(state.token && state.token.trim());
  }

  async function requestAny(path, options = {}) {
    if (!hasToken()) {
      throw new Error("Bearer token required");
    }
    const response = await fetch(joinUrl(state.baseUrl, path), {
      ...options,
      headers: authHeaders({
        Accept: "application/json",
        ...(options.headers || {}),
      }),
    });

    if (!response.ok) {
      const text = await response.text().catch(() => "");
      throw new Error(`${response.status} ${response.statusText}${text ? ` - ${text}` : ""}`);
    }
    if (response.status === 204) return null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return response.text();
  }

  async function requestJson(path, options = {}) {
    const data = await requestAny(path, options);
    if (data === null || typeof data === "object") return data;
    throw new Error(`Expected JSON from ${path}`);
  }

  async function safeRequest(paths) {
    let lastError = null;
    for (const path of paths) {
      try {
        return await requestAny(path);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError || new Error("Unable to reach backend");
  }

  function renderConnectionState(message, kind = "info") {
    ui.connectionState.textContent = message;
    ui.connectionState.className = `telemetry-value ${kind === "error" ? "status-bad" : kind === "warn" ? "status-warn" : ""}`.trim();
  }

  function setInteractionLock(locked, message, mode = "idle") {
    const controls = [
      ui.searchQuery,
      ui.wingFilter,
      ui.roomFilter,
      ui.searchButton,
      ...ui.taxonomyGrid.querySelectorAll("button"),
      ...ui.drawerList.querySelectorAll("button"),
    ];
    controls.forEach((node) => {
      if (node) node.disabled = locked;
    });
    ui.searchLock.textContent = message;
    ui.searchLock.style.color = mode === "warn" ? "var(--warn)" : mode === "muted" ? "var(--muted)" : locked ? "var(--warn)" : "var(--accent)";
    ui.searchLock.style.background =
      mode === "warn"
        ? "rgba(138, 90, 23, 0.08)"
        : mode === "muted"
          ? "rgba(94, 106, 118, 0.08)"
          : locked
            ? "rgba(138, 90, 23, 0.08)"
            : "rgba(33, 78, 117, 0.08)";
  }

  function fmtCount(value) {
    if (value === null || value === undefined || value === "") return "-";
    const num = Number(value);
    return Number.isFinite(num) ? num.toLocaleString() : String(value);
  }

  function pick(obj, keys, fallback = "-") {
    if (!obj || typeof obj !== "object") return fallback;
    for (const key of keys) {
      const value = key.split(".").reduce((acc, part) => (acc && typeof acc === "object" ? acc[part] : undefined), obj);
      if (value !== undefined && value !== null && value !== "") return value;
    }
    return fallback;
  }

  function textValue(value) {
    if (value === null || value === undefined || value === "") return "-";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function renderDisconnectedState(message) {
    state.miningActive = false;
    state.lastSnapshot = null;
    state.selectedDrawerId = null;
    state.selectedScope = { wing: "", room: "" };
    resetOntologyState("Token required to load ontology runs.");
    setInteractionLock(true, "Token required", "muted");
    renderConnectionState(message, "warn");
    ui.serviceHealth.textContent = "Disconnected";
    ui.serviceHealth.className = "metric-value status-warn";
    ui.serviceHealthHint.textContent = "Enter a bearer token to load backend telemetry.";
    ui.drawerCount.textContent = "-";
    ui.drawerCountHint.textContent = "Waiting for authenticated telemetry";
    ui.embeddingDevice.textContent = "Unavailable";
    ui.embeddingDeviceHint.textContent = "No backend data loaded yet";
    ui.miningState.textContent = "Token required";
    ui.miningState.className = "metric-value status-warn";
    ui.miningStateHint.textContent = "Save a bearer token to enable telemetry refresh.";
    ui.localaiStatus.textContent = "Not configured";
    ui.checkpointStatus.textContent = "Not configured";
    ui.lastRefresh.textContent = "-";
    ui.wingFilter.value = "";
    ui.roomFilter.value = "";
    ui.taxonomyStatus.textContent = "Token required to load taxonomy.";
    ui.searchSummary.textContent = "Token required";
    ui.drawerScope.textContent = "Token required";
    ui.detailTitle.textContent = "Nothing selected";
    ui.taxonomyGrid.replaceChildren();
    populateWingOptions([]);
    ui.searchResults.innerHTML = `<div class="empty-state">Enter and save a bearer token to search drawers.</div>`;
    ui.drawerList.innerHTML = `<div class="empty-state">Enter and save a bearer token to browse drawers.</div>`;
    ui.drawerDetail.innerHTML = `<div class="empty-state">Drawer detail is unavailable until authenticated telemetry loads.</div>`;
  }

  function buildChips(values) {
    const items = Array.isArray(values) ? values.filter(Boolean) : [];
    if (!items.length) return "";
    return `<div class="chips">${items.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div>`;
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function isObject(value) {
    return Boolean(value && typeof value === "object" && !Array.isArray(value));
  }

  function ensureArray(value) {
    if (Array.isArray(value)) return value;
    if (isObject(value)) return Object.values(value);
    return [];
  }

  function formatTimestamp(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
  }

  function formatDuration(value) {
    const total = Number(value);
    if (!Number.isFinite(total) || total < 0) return "-";
    const seconds = Math.round(total);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainder = seconds % 60;
    if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
    if (minutes > 0) return `${minutes}m ${String(remainder).padStart(2, "0")}s`;
    return `${remainder}s`;
  }

  function formatBytes(value) {
    const bytes = Number(value);
    if (!Number.isFinite(bytes) || bytes < 0) return "-";
    if (bytes < 1024) return `${bytes} B`;
    const units = ["KB", "MB", "GB", "TB"];
    let current = bytes / 1024;
    let unit = 0;
    while (current >= 1024 && unit < units.length - 1) {
      current /= 1024;
      unit += 1;
    }
    return `${current >= 10 ? current.toFixed(0) : current.toFixed(1)} ${units[unit]}`;
  }

  function formatPercent(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return "-";
    return `${Math.round(number)}%`;
  }

  function formatMaybeEta(value) {
    if (value === null || value === undefined || value === "") return "-";
    if (typeof value === "number") {
      return value > 1_000_000_000 ? formatTimestamp(value) : formatDuration(value);
    }
    const asNumber = Number(value);
    if (Number.isFinite(asNumber)) {
      return asNumber > 1_000_000_000 ? formatTimestamp(asNumber) : formatDuration(asNumber);
    }
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleString();
  }

  function rowChip(label, value) {
    return `<span class="row-chip">${escapeHtml(`${label}: ${textValue(value)}`)}</span>`;
  }

  function runIdFor(run) {
    if (!run || typeof run !== "object") return "";
    return String(run.run_id || run.id || run.runId || "");
  }

  function artifactKeyFor(artifact) {
    if (!artifact || typeof artifact !== "object") return "";
    return String(artifact.artifact_key || artifact.relative_path || artifact.path || artifact.id || "");
  }

  function runPriority(run) {
    const status = String(pick(run, ["status"], "")).toLowerCase();
    const selected = runIdFor(run) === state.selectedOntologyRunId;
    const current = Boolean(pick(run, ["current", "is_current", "selected", "active"], false)) || status === "running";
    if (selected) return 4;
    if (current) return 3;
    if (status === "completed") return 2;
    if (status === "pending") return 1;
    return 0;
  }

  function normalizeOntologyRuns(payload) {
    const source = Array.isArray(payload)
      ? payload
      : ensureArray(payload?.runs || payload?.items || payload?.results || payload?.data || payload?.records);
    return source.filter(isObject).map((run) => run);
  }

  function normalizeOntologyArtifacts(payload) {
    const source = Array.isArray(payload)
      ? payload
      : ensureArray(payload?.artifacts || payload?.items || payload?.results || payload?.data || payload?.records);
    return source.filter(isObject).map((artifact) => artifact);
  }

  function normalizeOntologyPreview(payload) {
    const source = Array.isArray(payload)
      ? payload
      : ensureArray(payload?.preview || payload?.items || payload?.results || payload?.data || payload?.records);
    return source.filter(isObject).map((item) => item);
  }

  function chooseOntologyRunId(runs) {
    const ids = runs.map(runIdFor).filter(Boolean);
    if (state.selectedOntologyRunId && ids.includes(state.selectedOntologyRunId)) {
      return state.selectedOntologyRunId;
    }
    const prioritized = [...runs].sort((a, b) => {
      const priorityDiff = runPriority(b) - runPriority(a);
      if (priorityDiff) return priorityDiff;
      const timeDiff = new Date(pick(b, ["updated_at", "started_at"], 0)).getTime() - new Date(pick(a, ["updated_at", "started_at"], 0)).getTime();
      if (Number.isFinite(timeDiff) && timeDiff !== 0) return timeDiff;
      return runIdFor(a).localeCompare(runIdFor(b));
    });
    return runIdFor(prioritized[0]) || null;
  }

  function ontologyCountValue(progress, keys, fallback = "-") {
    if (!progress || typeof progress !== "object") return fallback;
    for (const key of keys) {
      const value = key.split(".").reduce((acc, part) => (acc && typeof acc === "object" ? acc[part] : undefined), progress);
      if (value !== undefined && value !== null && value !== "") {
        return fmtCount(value);
      }
    }
    return fallback;
  }

  function resolveRunPayload(detail, fallback) {
    if (isObject(detail?.run)) return detail.run;
    if (isObject(detail?.progress) && !runIdFor(detail)) return fallback || detail.progress;
    return isObject(detail) ? detail : fallback || {};
  }

  function resolveProgressPayload(detail, fallback) {
    if (isObject(detail?.progress)) return detail.progress;
    if (isObject(detail) && (detail.current_phase_progress || detail.totals || detail.status || detail.run_kind)) return detail;
    if (isObject(detail?.run?.progress)) return detail.run.progress;
    return isObject(fallback?.progress) ? fallback.progress : fallback || {};
  }

  function resetOntologyState(message) {
    state.ontologyRuns = [];
    state.selectedOntologyRunId = null;
    state.selectedArtifactKey = null;
    ui.ontologyRunState.textContent = "Token required";
    ui.ontologyRunStatus.textContent = message;
    ui.ontologyRunSummary.textContent = "Token required";
    ui.ontologyRunList.replaceChildren();
    ui.ontologyRunTitle.textContent = "No run selected";
    ui.ontologyRunMeta.textContent = "Token required";
    ui.ontologyProgressBar.className = "progress-fill is-unknown";
    ui.ontologyProgressBar.style.width = "28%";
    ui.ontologyProgressLabel.textContent = "No run loaded";
    ui.ontologyProgressPercent.textContent = "-";
    ui.ontologyProgressStats.replaceChildren();
    ui.ontologyProgressDetail.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
    ui.ontologyArtifactSummary.textContent = "Token required";
    ui.ontologyArtifactList.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
    ui.ontologyArtifactDetail.innerHTML = `<p>${escapeHtml(message)}</p>`;
    ui.ontologyPreviewStatus.textContent = "Token required";
    ui.ontologyPreviewList.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
  }

  function renderOntologyMetricTiles(items) {
    const fragment = document.createDocumentFragment();
    items.forEach((item) => {
      const tile = document.createElement("div");
      tile.className = "stat-tile";
      tile.innerHTML = `
        <div class="stat-label">${escapeHtml(item.label)}</div>
        <div class="stat-value">${escapeHtml(item.value)}</div>
        <div class="stat-note">${escapeHtml(item.note)}</div>
      `;
      fragment.appendChild(tile);
    });
    ui.ontologyProgressStats.replaceChildren(fragment);
  }

  function renderOntologyProgress(run, detail) {
    const runData = resolveRunPayload(detail, run);
    const progress = resolveProgressPayload(detail, runData);
    const runId = runIdFor(runData) || runIdFor(run) || "No run selected";
    const status = String(pick(progress, ["status", "current_phase_status"], pick(runData, ["status"], "unknown")));
    const currentPhase = textValue(pick(progress, ["current_phase"], pick(runData, ["current_phase"], "-")));
    const phaseStatus = textValue(pick(progress, ["current_phase_status"], "-"));
    const phaseProgress = isObject(progress.current_phase_progress) ? progress.current_phase_progress : {};
    const total = Number(phaseProgress.total);
    const processed = Number(phaseProgress.processed);
    const percent = Number.isFinite(total) && total > 0 && Number.isFinite(processed) ? Math.max(0, Math.min(100, (processed / total) * 100)) : null;
    const accepted = pick(phaseProgress, ["accepted"], "-");
    const unresolved = pick(phaseProgress, ["unresolved"], "-");
    const errors = pick(phaseProgress, ["errors"], "-");
    const elapsedSeconds = pick(progress, ["elapsed_seconds"], pick(runData, ["elapsed_seconds"], null));
    const etaValue = pick(progress, ["eta_seconds", "remaining_seconds", "estimated_remaining_seconds", "eta", "eta_at", "estimated_eta"], null);
    const phaseOrder = Array.isArray(progress.phase_order) ? progress.phase_order : [];

    ui.ontologyRunTitle.textContent = runId;
    ui.ontologyRunMeta.textContent = [
      `Status ${textValue(status)}`,
      currentPhase && currentPhase !== "-" ? `Phase ${currentPhase}` : null,
      phaseStatus && phaseStatus !== "-" ? `Phase state ${phaseStatus}` : null,
      elapsedSeconds !== null && elapsedSeconds !== undefined ? `Elapsed ${formatDuration(elapsedSeconds)}` : null,
      etaValue !== null && etaValue !== undefined ? `ETA ${formatMaybeEta(etaValue)}` : null,
    ].filter(Boolean).join(" · ");
    ui.ontologyRunState.textContent = textValue(status);
    ui.ontologyRunState.className = `state-pill ${String(status).toLowerCase().includes("fail") || String(status).toLowerCase().includes("cancel") ? "status-bad" : String(status).toLowerCase().includes("run") ? "status-warn" : ""}`.trim();
    ui.ontologyProgressLabel.textContent = `${runId} · ${currentPhase !== "-" ? currentPhase : "phase unknown"}`;
    ui.ontologyProgressPercent.textContent = percent === null ? "-" : formatPercent(percent);
    ui.ontologyProgressBar.className = `progress-fill${percent === null ? " is-unknown" : ""}`;
    ui.ontologyProgressBar.style.width = percent === null ? "28%" : `${percent}%`;

    renderOntologyMetricTiles([
      { label: "Processed", value: fmtCount(processed), note: `Unit ${textValue(pick(phaseProgress, ["unit"], "-"))}` },
      { label: "Total", value: fmtCount(total), note: `Accepted ${fmtCount(accepted)}` },
      { label: "Unresolved", value: fmtCount(unresolved), note: `Errors ${fmtCount(errors)}` },
      { label: "Elapsed", value: formatDuration(elapsedSeconds), note: etaValue !== null && etaValue !== undefined ? `ETA ${formatMaybeEta(etaValue)}` : "ETA unavailable" },
    ]);

    const totals = isObject(progress.totals) ? progress.totals : {};
    const lastRecord = isObject(progress.last_record) ? progress.last_record : {};
    const details = [
      `<div><strong>Run kind</strong>: ${escapeHtml(textValue(pick(progress, ["run_kind"], pick(runData, ["run_kind"], "-"))))}</div>`,
      `<div><strong>Source wing</strong>: ${escapeHtml(textValue(pick(progress, ["source_wing"], pick(runData, ["source_wing"], "-"))))}</div>`,
      `<div><strong>Phase order</strong>: ${escapeHtml(Array.isArray(phaseOrder) && phaseOrder.length ? phaseOrder.join(" → ") : "-")}</div>`,
      `<div><strong>Source drawers</strong>: ${escapeHtml(ontologyCountValue(totals, ["source_drawers_total"], "-"))}</div>`,
      `<div><strong>Drawers processed</strong>: ${escapeHtml(ontologyCountValue(totals, ["source_drawers_processed"], "-"))}</div>`,
      `<div><strong>Routes accepted</strong>: ${escapeHtml(ontologyCountValue(totals, ["routes_accepted"], "-"))}</div>`,
      `<div><strong>Routes unresolved</strong>: ${escapeHtml(ontologyCountValue(totals, ["routes_unresolved"], "-"))}</div>`,
      `<div><strong>Phase records</strong>: ${escapeHtml(ontologyCountValue(totals, ["phase_records_written"], "-"))}</div>`,
      `<div><strong>Warnings</strong>: ${escapeHtml(ontologyCountValue(progress, ["warning_count"], pick(runData, ["warning_count"], "-")))}</div>`,
      `<div><strong>Errors</strong>: ${escapeHtml(ontologyCountValue(progress, ["error_count"], pick(runData, ["error_count"], "-")))}</div>`,
      lastRecord.phase ? `<div><strong>Last record</strong>: ${escapeHtml([lastRecord.phase, lastRecord.relative_path, lastRecord.subject_id].filter(Boolean).join(" · "))}</div>` : "",
    ].filter(Boolean).join("");
    ui.ontologyProgressDetail.innerHTML = details || `<div class="empty-state">No progress detail returned.</div>`;
  }

  function renderOntologyRunList(runs) {
    state.ontologyRuns = Array.isArray(runs) ? runs : [];
    ui.ontologyRunList.replaceChildren();
    const rows = state.ontologyRuns;
    ui.ontologyRunSummary.textContent = rows.length ? `${rows.length} run${rows.length === 1 ? "" : "s"} loaded` : "No runs";
    if (!rows.length) {
      ui.ontologyRunStatus.textContent = "No ontology runs returned.";
      ui.ontologyRunList.innerHTML = `<div class="empty-state">No ontology runs returned.</div>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    rows.forEach((run) => {
      const runId = runIdFor(run);
      const row = document.createElement("button");
      row.type = "button";
      row.className = `run-row${runId && runId === state.selectedOntologyRunId ? " active" : ""}`;
      row.dataset.runId = runId;
      const status = textValue(pick(run, ["status"], "unknown"));
      const phase = textValue(pick(run, ["current_phase"], "-"));
      const updated = formatTimestamp(pick(run, ["updated_at", "started_at"], ""));
      row.innerHTML = `
        <div class="row-head">
          <div class="row-title">${escapeHtml(runId || "Run")}</div>
          <span class="row-chip">${escapeHtml(status)}</span>
        </div>
        <div class="row-meta">
          ${phase && phase !== "-" ? `<span>${escapeHtml(`Phase ${phase}`)}</span>` : ""}
          ${pick(run, ["current_phase_status"], "") ? `<span>${escapeHtml(`State ${textValue(pick(run, ["current_phase_status"], "-"))}`)}</span>` : ""}
          ${updated ? `<span>${escapeHtml(updated)}</span>` : ""}
        </div>
        <div class="row-subtle">${escapeHtml([
          `Elapsed ${formatDuration(pick(run, ["elapsed_seconds"], null))}`,
          `Processed ${fmtCount(pick(run, ["source_drawers_processed", "processed"], "-"))}`,
        ].join(" · "))}</div>
      `;
      row.addEventListener("click", () => {
        if (runId && runId !== state.selectedOntologyRunId) {
          state.selectedOntologyRunId = runId;
          state.selectedArtifactKey = null;
          refreshOntology().catch((error) => renderConnectionState(error.message, "error"));
        }
      });
      fragment.appendChild(row);
    });
    ui.ontologyRunList.appendChild(fragment);
  }

  function renderOntologyArtifactDetail(artifact) {
    if (!artifact) {
      ui.ontologyArtifactDetail.innerHTML = `<p>No artifact selected.</p>`;
      return;
    }
    const metaPairs = [
      ["Artifact", artifact.artifact_key || artifact.relative_path],
      ["Path", artifact.relative_path],
      ["Schema", artifact.schema_name],
      ["Version", artifact.schema_version],
      ["Kind", artifact.artifact_kind],
      ["Phase", artifact.phase],
      ["Content type", artifact.content_type],
      ["Status", artifact.status],
      ["Dashboard safe", artifact.dashboard_safe],
      ["Privacy", artifact.privacy_level],
      ["Records", artifact.records],
      ["Bytes", formatBytes(artifact.bytes)],
      ["Updated", formatTimestamp(artifact.updated_at)],
    ].filter(([, value]) => value !== undefined && value !== null && value !== "");
    ui.ontologyArtifactDetail.innerHTML = `
      <div class="artifact-detail">
        ${buildChips(metaPairs.map(([label, value]) => `${label}: ${textValue(value)}`))}
        ${metaPairs.map(([label, value]) => `<div><strong>${escapeHtml(label)}</strong>: ${escapeHtml(textValue(value))}</div>`).join("")}
        <div class="row-subtle">${artifact.dashboard_safe ? "Dashboard-safe metadata only. No full artifact body is fetched here." : "Restricted artifact. Metadata only; preview content is intentionally withheld."}</div>
      </div>
    `;
  }

  function renderOntologyArtifactList(artifacts) {
    const rows = Array.isArray(artifacts) ? artifacts : [];
    ui.ontologyArtifactList.replaceChildren();
    ui.ontologyArtifactSummary.textContent = rows.length ? `${rows.length} artifact${rows.length === 1 ? "" : "s"}` : "No artifacts";
    if (!rows.length) {
      ui.ontologyArtifactList.innerHTML = `<div class="empty-state">No artifacts indexed yet for this run.</div>`;
      ui.ontologyArtifactDetail.innerHTML = `<p>No artifacts indexed yet for this run.</p>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    rows.forEach((artifact) => {
      const key = artifactKeyFor(artifact);
      const row = document.createElement("button");
      row.type = "button";
      row.className = `artifact-row${key && key === state.selectedArtifactKey ? " active" : ""}`;
      row.dataset.artifactKey = key;
      row.innerHTML = `
        <div class="row-head">
          <div class="row-title">${escapeHtml(artifact.artifact_key || artifact.relative_path || key || "Artifact")}</div>
          <span class="row-chip">${escapeHtml(artifact.dashboard_safe ? "safe" : "restricted")}</span>
        </div>
        <div class="row-meta">
          <span>${escapeHtml(artifact.artifact_kind || "artifact")}</span>
          <span>${escapeHtml(artifact.privacy_level || "privacy?")}</span>
          <span>${escapeHtml(artifact.status || "status?")}</span>
        </div>
        <div class="artifact-summary">${escapeHtml([
          artifact.relative_path,
          artifact.records !== undefined ? `${fmtCount(artifact.records)} records` : null,
          artifact.bytes !== undefined ? formatBytes(artifact.bytes) : null,
        ].filter(Boolean).join(" · ") || "No artifact metadata returned.")}</div>
      `;
      row.addEventListener("click", () => {
        state.selectedArtifactKey = key;
        renderOntologyArtifactList(rows);
        renderOntologyArtifactDetail(artifact);
      });
      fragment.appendChild(row);
    });
    ui.ontologyArtifactList.appendChild(fragment);
    const selected = rows.find((artifact) => artifactKeyFor(artifact) === state.selectedArtifactKey) || rows[0];
    if (selected) {
      state.selectedArtifactKey = artifactKeyFor(selected);
      renderOntologyArtifactDetail(selected);
    }
  }

  function renderOntologyPreview(previewRows) {
    const rows = Array.isArray(previewRows) ? previewRows : [];
    ui.ontologyPreviewStatus.textContent = rows.length ? `${rows.length} preview item${rows.length === 1 ? "" : "s"}` : "No unresolved preview";
    ui.ontologyPreviewList.replaceChildren();
    if (!rows.length) {
      ui.ontologyPreviewList.innerHTML = `<div class="empty-state">No bounded unresolved preview data returned for this run.</div>`;
      return;
    }

    const fragment = document.createDocumentFragment();
    rows.slice(0, 12).forEach((item) => {
      const row = document.createElement("article");
      row.className = "preview-row";
      const candidateIds = Array.isArray(item.candidate_ids) ? item.candidate_ids.filter(Boolean) : [];
      row.innerHTML = `
        <div class="row-head">
          <div class="row-title">${escapeHtml(item.source_drawer_id || item.subject_id || item.source_id || "Unresolved item")}</div>
          <span class="row-chip">${escapeHtml(item.unresolved_status || item.reason_code || "preview")}</span>
        </div>
        <div class="row-meta">
          <span>${escapeHtml(item.source_wing || "wing?")}</span>
          <span>${escapeHtml(item.source_room || "room?")}</span>
          <span>${escapeHtml(item.next_action || "next action?")}</span>
        </div>
        <div class="preview-summary">${escapeHtml([
          item.reason_detail,
          candidateIds.length ? `${candidateIds.length} candidate${candidateIds.length === 1 ? "" : "s"}` : null,
          item.route_confidence !== undefined && item.route_confidence !== null ? `Confidence ${item.route_confidence}` : null,
        ].filter(Boolean).join(" · ") || "No preview summary returned.")}</div>
        ${item.source_excerpt ? `<pre>${escapeHtml(item.source_excerpt)}</pre>` : ""}
      `;
      fragment.appendChild(row);
    });
    ui.ontologyPreviewList.appendChild(fragment);
  }

  async function refreshOntology() {
    if (!hasToken()) {
      resetOntologyState("Token required to load ontology runs.");
      return;
    }

    try {
      const payload = await requestJson("/api/ontology/runs");
      const runs = normalizeOntologyRuns(payload);
      if (!runs.length) {
        state.selectedOntologyRunId = null;
        state.selectedArtifactKey = null;
        ui.ontologyRunState.textContent = "Idle";
        ui.ontologyRunState.className = "state-pill";
        ui.ontologyRunStatus.textContent = "No ontology runs returned.";
        ui.ontologyRunSummary.textContent = "No runs";
        ui.ontologyRunList.innerHTML = `<div class="empty-state">No ontology runs returned.</div>`;
        ui.ontologyRunTitle.textContent = "No run selected";
        ui.ontologyRunMeta.textContent = "No ontology run data available.";
        ui.ontologyProgressBar.className = "progress-fill is-unknown";
        ui.ontologyProgressBar.style.width = "28%";
        ui.ontologyProgressLabel.textContent = "No run loaded";
        ui.ontologyProgressPercent.textContent = "-";
        ui.ontologyProgressStats.replaceChildren();
        ui.ontologyProgressDetail.innerHTML = `<div class="empty-state">No progress data returned.</div>`;
        ui.ontologyArtifactSummary.textContent = "No runs";
        ui.ontologyArtifactList.innerHTML = `<div class="empty-state">Select a run to inspect artifacts.</div>`;
        ui.ontologyArtifactDetail.innerHTML = `<p>Select a run to inspect artifacts.</p>`;
        ui.ontologyPreviewStatus.textContent = "No runs";
        ui.ontologyPreviewList.innerHTML = `<div class="empty-state">No unresolved preview available.</div>`;
        return;
      }

      state.ontologyRuns = runs;
      const selectedRunId = chooseOntologyRunId(runs);
      state.selectedOntologyRunId = selectedRunId;
      renderOntologyRunList(runs);

      const selectedRun = runs.find((run) => runIdFor(run) === selectedRunId) || runs[0];
      ui.ontologyRunStatus.textContent = selectedRunId ? `Loaded ${runs.length} run${runs.length === 1 ? "" : "s"}` : "Run list loaded";
      if (!selectedRunId) {
        return;
      }

      const detailResult = await Promise.allSettled([
        requestJson(`/api/ontology/runs/${encodeURIComponent(selectedRunId)}`),
        requestJson(`/api/ontology/runs/${encodeURIComponent(selectedRunId)}/artifacts`),
        requestJson(`/api/ontology/runs/${encodeURIComponent(selectedRunId)}/unresolved-preview`),
      ]);
      const [detailOutcome, artifactsOutcome, previewOutcome] = detailResult;

      const detail = detailOutcome.status === "fulfilled" ? detailOutcome.value : selectedRun;
      const artifacts = artifactsOutcome.status === "fulfilled" ? normalizeOntologyArtifacts(artifactsOutcome.value) : [];
      const preview = previewOutcome.status === "fulfilled" ? normalizeOntologyPreview(previewOutcome.value) : [];

      renderOntologyRunList(runs);
      renderOntologyProgress(selectedRun, detail);
      renderOntologyArtifactList(artifacts);
      renderOntologyPreview(preview);

      if (artifactsOutcome.status === "rejected") {
        ui.ontologyArtifactSummary.textContent = `Artifacts error: ${artifactsOutcome.reason.message || artifactsOutcome.reason}`;
        ui.ontologyArtifactList.innerHTML = `<div class="empty-state status-bad">${escapeHtml(artifactsOutcome.reason.message || String(artifactsOutcome.reason))}</div>`;
      }
      if (previewOutcome.status === "rejected") {
        ui.ontologyPreviewStatus.textContent = `Preview error: ${previewOutcome.reason.message || previewOutcome.reason}`;
        ui.ontologyPreviewList.innerHTML = `<div class="empty-state status-bad">${escapeHtml(previewOutcome.reason.message || String(previewOutcome.reason))}</div>`;
      }
      if (detailOutcome.status === "rejected") {
        ui.ontologyRunMeta.textContent = `Detail error: ${detailOutcome.reason.message || detailOutcome.reason}`;
        ui.ontologyProgressDetail.innerHTML = `<div class="empty-state status-bad">${escapeHtml(detailOutcome.reason.message || String(detailOutcome.reason))}</div>`;
      }
      if (!artifacts.length) {
        ui.ontologyArtifactSummary.textContent = "No artifacts";
      }
      if (!preview.length) {
        ui.ontologyPreviewStatus.textContent = "No unresolved preview";
      }
      ui.ontologyRunStatus.textContent = `Selected ${selectedRunId}`;
    } catch (error) {
      ui.ontologyRunState.textContent = "Error";
      ui.ontologyRunState.className = "state-pill status-bad";
      ui.ontologyRunStatus.textContent = `Unable to load ontology runs: ${error.message}`;
      ui.ontologyRunSummary.textContent = "Error";
      ui.ontologyRunList.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
      ui.ontologyRunTitle.textContent = "Ontology unavailable";
      ui.ontologyRunMeta.textContent = error.message;
      ui.ontologyProgressBar.className = "progress-fill is-unknown";
      ui.ontologyProgressBar.style.width = "28%";
      ui.ontologyProgressLabel.textContent = "Ontology unavailable";
      ui.ontologyProgressPercent.textContent = "-";
      ui.ontologyProgressStats.replaceChildren();
      ui.ontologyProgressDetail.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
      ui.ontologyArtifactSummary.textContent = "Error";
      ui.ontologyArtifactList.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
      ui.ontologyArtifactDetail.innerHTML = `<p class="status-bad">${escapeHtml(error.message)}</p>`;
      ui.ontologyPreviewStatus.textContent = "Error";
      ui.ontologyPreviewList.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
    }
  }

  function summarizeTelemetry(snapshot) {
    const localai = pick(snapshot, ["localai_status", "localai.status", "telemetry.localai.status"], null);
    const checkpoint = pick(snapshot, ["checkpoint", "checkpoint_status", "telemetry.checkpoint"], null);
    const embedding = pick(snapshot, ["embedding_device", "embedding.device", "telemetry.embedding_device"], "-");
    const miningActive = Boolean(pick(snapshot, ["mining_active", "mining.active", "telemetry.mining_active"], false));
    const drawerCount = pick(snapshot, ["drawer_count", "total_drawers", "stats.drawers", "telemetry.drawer_count"], "-");
    const health = pick(snapshot, ["health", "service_health", "status", "telemetry.health"], "unknown");

    ui.serviceHealth.textContent = textValue(health);
    ui.serviceHealth.className = `metric-value ${String(health).toLowerCase().includes("ok") || String(health).toLowerCase().includes("healthy") ? "status-good" : ""}`.trim();
    ui.serviceHealthHint.textContent = pick(snapshot, ["health_detail", "service_health_detail", "telemetry.health_detail"], "Backend health status");
    ui.drawerCount.textContent = fmtCount(drawerCount);
    ui.drawerCountHint.textContent = pick(snapshot, ["drawer_hint", "stats.note", "telemetry.drawer_hint"], "Total indexed drawers");
    ui.embeddingDevice.textContent = textValue(embedding);
    ui.embeddingDeviceHint.textContent = pick(snapshot, ["embedding_device_hint", "telemetry.embedding_device_hint"], "Resolved backend device");
    ui.miningState.textContent = miningActive ? "Active" : "Idle";
    ui.miningState.className = `metric-value ${miningActive ? "status-warn" : "status-good"}`.trim();
    ui.miningStateHint.textContent = miningActive ? "Telemetry-only mode engaged" : "Search and browsing enabled";
    ui.localaiStatus.textContent = formatOptionalTelemetry(localai);
    ui.checkpointStatus.textContent = formatOptionalTelemetry(checkpoint);
    ui.lastRefresh.textContent = new Date().toLocaleString();
    state.miningActive = miningActive;
    state.lastSnapshot = snapshot;
  }

  function formatOptionalTelemetry(value) {
    if (value === undefined) return "Not configured";
    if (value === null || value === "") return "Unavailable";
    return textValue(value);
  }

  function renderTaxonomy(taxonomy) {
    state.taxonomy = normalizeTaxonomy(taxonomy);
    ui.taxonomyGrid.replaceChildren();
    const wings = state.taxonomy;
    if (!wings.length) {
      ui.taxonomyStatus.textContent = state.miningActive ? "Taxonomy browser is disabled during active mining." : "No taxonomy data returned.";
      populateWingOptions([]);
      return;
    }
    ui.taxonomyStatus.textContent = `${wings.length} wings available`;
    populateWingOptions(wings);
    const fragment = document.createDocumentFragment();
    wings.forEach((wingEntry) => {
      const wing = typeof wingEntry === "string" ? wingEntry : wingEntry.wing || wingEntry.name || wingEntry.id || "unknown";
      const rooms = Array.isArray(wingEntry.rooms)
        ? wingEntry.rooms
        : wingEntry.rooms && typeof wingEntry.rooms === "object"
          ? Object.entries(wingEntry.rooms).map(([room, count]) => ({ room, count }))
          : [];
      const tile = document.createElement("div");
      tile.className = "taxonomy-tile";
      tile.innerHTML = `
        <button type="button" data-wing="${escapeHtml(wing)}">
          <div class="result-title">${escapeHtml(wing)}</div>
          <div class="taxonomy-meta">${rooms.length ? `${rooms.length} rooms` : "No room breakdown"}</div>
          ${rooms.slice(0, 4).map((room) => `<span class="chip">${escapeHtml(room.room || room[0] || room.name || "room")} ${room.count !== undefined ? `(${fmtCount(room.count)})` : ""}</span>`).join("")}
        </button>
      `;
      fragment.appendChild(tile);
    });
    ui.taxonomyGrid.appendChild(fragment);
    ui.taxonomyGrid.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        if (state.miningActive) return;
        const wing = button.dataset.wing || "";
        ui.wingFilter.value = wing;
        ui.roomFilter.value = "";
        state.selectedScope = { wing, room: "" };
        ui.wingFilter.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
  }

  function populateWingOptions(wings) {
    const currentWing = ui.wingFilter.value.trim();
    const items = Array.isArray(wings)
      ? wings
          .map((wingEntry) => (typeof wingEntry === "string" ? wingEntry : wingEntry.wing || wingEntry.name || wingEntry.id || ""))
          .filter(Boolean)
      : [];
    const unique = [...new Set(items)].sort((a, b) => a.localeCompare(b));
    ui.wingFilter.replaceChildren(new Option("All wings", ""));
    unique.forEach((wing) => {
      ui.wingFilter.add(new Option(wing, wing));
    });
    if (currentWing && !unique.includes(currentWing)) {
      ui.wingFilter.add(new Option(currentWing, currentWing));
    }
    ui.wingFilter.value = currentWing;
  }

  function normalizeTaxonomy(taxonomy) {
    if (Array.isArray(taxonomy)) return taxonomy;
    if (!taxonomy || typeof taxonomy !== "object") return [];
    return Object.entries(taxonomy)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([wing, rooms]) => ({
        wing,
        rooms: rooms && typeof rooms === "object"
          ? Object.entries(rooms)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([room, count]) => ({ room, count }))
          : [],
      }));
  }

  function renderDrawers(drawers) {
    state.drawers = drawers;
    ui.drawerList.replaceChildren();
    const rows = Array.isArray(drawers) ? drawers : [];
    ui.drawerScope.textContent = state.selectedScope.wing || state.selectedScope.room ? scopeLabel(state.selectedScope) : "All drawers";
    if (!rows.length) {
      ui.drawerList.innerHTML = `<div class="empty-state">No drawers returned for this scope.</div>`;
      return;
    }
    const fragment = document.createDocumentFragment();
    rows.forEach((drawer) => {
      const id = drawer.id || drawer.drawer_id || drawer.source_drawer_id || drawer.source_file || "";
      const row = document.createElement("button");
      row.type = "button";
      row.className = `drawer-row${state.selectedDrawerId === id ? " active" : ""}`;
      row.dataset.drawerId = id;
      row.innerHTML = `
        <div class="drawer-row-title">${escapeHtml(drawer.title || drawer.name || id || "Drawer")}</div>
        <div class="drawer-row-meta">
          <span>${escapeHtml(drawer.wing || "wing?")}</span>
          <span>${escapeHtml(drawer.room || "room?")}</span>
          <span>${escapeHtml(drawer.source_file || drawer.source || "")}</span>
        </div>
        <div class="drawer-row-subtle">${escapeHtml(previewText(drawer.text || drawer.document || drawer.content || ""))}</div>
      `;
      row.addEventListener("click", () => {
        state.selectedDrawerId = id;
        renderDrawers(state.drawers);
        loadDrawerDetail(id, drawer);
      });
      fragment.appendChild(row);
    });
    ui.drawerList.appendChild(fragment);
    if (!state.selectedDrawerId && rows[0]) {
      state.selectedDrawerId = rows[0].id || rows[0].drawer_id || rows[0].source_drawer_id || rows[0].source_file || "";
      renderDrawers(state.drawers);
      renderDrawerDetail(rows[0]);
    }
  }

  function previewText(value) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    if (!text) return "No preview text provided.";
    return text.length > 160 ? `${text.slice(0, 160)}...` : text;
  }

  function scopeLabel(scope) {
    const parts = [];
    if (scope.wing) parts.push(`Wing ${scope.wing}`);
    if (scope.room) parts.push(`Room ${scope.room}`);
    return parts.join(" / ") || "All drawers";
  }

  function renderDrawerDetail(drawer) {
    const id = drawer.id || drawer.drawer_id || drawer.source_drawer_id || drawer.source_file || "drawer";
    ui.detailTitle.textContent = id;
    const metaPairs = [
      ["Wing", drawer.wing],
      ["Room", drawer.room],
      ["Hall", drawer.hall],
      ["Source", drawer.source_file],
      ["Chunk", drawer.chunk_index],
      ["Similarity", drawer.similarity],
      ["BM25", drawer.bm25_score],
    ].filter(([, value]) => value !== undefined && value !== null && value !== "");
    const metadata = drawer.metadata && typeof drawer.metadata === "object" ? drawer.metadata : null;
    const extra = metadata ? Object.entries(metadata).slice(0, 12).map(([key, value]) => `<div><strong>${escapeHtml(key)}</strong>: ${escapeHtml(textValue(value))}</div>`).join("") : "";
    ui.drawerDetail.innerHTML = `
      <div class="detail-grid">
        ${buildChips(metaPairs.map(([label, value]) => `${label}: ${textValue(value)}`))}
        ${metaPairs.map(([label, value]) => `<div><strong>${escapeHtml(label)}</strong>: ${escapeHtml(textValue(value))}</div>`).join("")}
        ${extra ? `<div>${extra}</div>` : ""}
        <pre>${escapeHtml(drawer.text || drawer.document || drawer.content || drawer.preview || "No drawer text returned.")}</pre>
      </div>
    `;
  }

  function renderSearchResults(results) {
    const rows = Array.isArray(results) ? results : [];
    ui.searchResults.replaceChildren();
    ui.searchSummary.textContent = rows.length ? `${rows.length} hits` : "No hits";
    if (!rows.length) {
      ui.searchResults.innerHTML = `<div class="empty-state">No results for the current query.</div>`;
      return;
    }
    const fragment = document.createDocumentFragment();
    rows.forEach((result, index) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "result-item";
      item.innerHTML = `
        <div class="result-title">[${index + 1}] ${escapeHtml(result.title || result.id || result.source_file || "Result")}</div>
        <div class="result-meta">
          <span>${escapeHtml(result.wing || "wing?")}</span>
          <span>${escapeHtml(result.room || "room?")}</span>
          <span>${escapeHtml(result.source_file || "")}</span>
          <span>${escapeHtml(result.matched_via || "hybrid")}</span>
        </div>
        <div class="drawer-row-subtle">${escapeHtml(previewText(result.text || result.document || result.content || ""))}</div>
      `;
      item.addEventListener("click", () => {
        const id = result.id || result.drawer_id || result.source_drawer_id || "";
        if (id) {
          loadDrawerDetail(id, result);
        } else {
          renderDrawerDetail(result);
        }
      });
      fragment.appendChild(item);
    });
    ui.searchResults.appendChild(fragment);
  }

  function applyMiningLock() {
    setInteractionLock(state.miningActive, state.miningActive ? "Telemetry-only while mining" : "Search and browsing enabled", state.miningActive ? "warn" : "idle");
    ui.taxonomyStatus.textContent = state.miningActive
      ? "Telemetry-only: taxonomy browser is disabled while mining is active."
      : "Taxonomy browser ready.";
    if (state.miningActive) {
      ui.searchResults.innerHTML = `<div class="empty-state">Search is disabled while mining is active.</div>`;
      ui.drawerList.innerHTML = `<div class="empty-state">Drawer browser is disabled while mining is active.</div>`;
      ui.drawerDetail.innerHTML = `<div class="empty-state">Telemetry-only mode. Select details are suppressed while mining runs.</div>`;
    }
  }

  async function refreshOverview() {
    renderConnectionState("Refreshing...");
    const snapshot = await requestJson("/api/overview").catch(() => ({}));
    const body = snapshot && typeof snapshot === "object" ? snapshot : {};
    summarizeTelemetry(body);
    applyMiningLock();
    renderConnectionState("Connected");
    const tasks = [refreshOntology()];
    if (!state.miningActive) {
      tasks.push(refreshTaxonomy(), refreshDrawers());
    } else {
      renderTaxonomy([]);
      renderDrawers([]);
    }
    await Promise.allSettled(tasks);
  }

  async function refreshTaxonomy() {
    if (state.miningActive) return;
    const taxonomy = await safeRequest([
      "/dashboard/taxonomy",
      "/taxonomy",
      "/api/dashboard/taxonomy",
      "/api/taxonomy",
    ]);
    const data = Array.isArray(taxonomy) ? taxonomy : taxonomy.taxonomy || taxonomy.wings || taxonomy.rooms || [];
    renderTaxonomy(data);
  }

  async function refreshDrawers() {
    if (state.miningActive) return;
    state.selectedScope = {
      wing: ui.wingFilter.value.trim(),
      room: ui.roomFilter.value.trim(),
    };
    const path = buildDrawerPath();
    const payload = await requestJson(path);
    const drawers = payload.drawers || payload.results || payload.items || payload || [];
    renderDrawers(Array.isArray(drawers) ? drawers : []);
    updateRoomOptions(payload);
  }

  function buildDrawerPath() {
    const params = new URLSearchParams();
    if (ui.wingFilter.value.trim()) params.set("wing", ui.wingFilter.value.trim());
    if (ui.roomFilter.value.trim()) params.set("room", ui.roomFilter.value.trim());
    const query = params.toString();
    return `/api/drawers${query ? `?${query}` : ""}`;
  }

  async function loadDrawerDetail(id, fallback) {
    if (state.miningActive || !id) {
      renderDrawerDetail(fallback || {});
      return;
    }
    try {
      const payload = await requestJson(`/api/drawers/${encodeURIComponent(id)}`);
      renderDrawerDetail(payload && typeof payload === "object" ? payload : fallback || {});
    } catch {
      renderDrawerDetail(fallback || {});
    }
  }

  function updateRoomOptions(payload) {
    const currentWing = ui.wingFilter.value.trim();
    const rows = Array.isArray(payload?.taxonomy)
      ? payload.taxonomy
      : Array.isArray(state.taxonomy)
        ? state.taxonomy
        : [];
    const roomMap = new Map();
    rows.forEach((wingEntry) => {
      const wing = typeof wingEntry === "string" ? wingEntry : wingEntry.wing || wingEntry.name;
      if (currentWing && wing !== currentWing) return;
      const rooms = Array.isArray(wingEntry.rooms)
        ? wingEntry.rooms
        : wingEntry.rooms && typeof wingEntry.rooms === "object"
          ? Object.entries(wingEntry.rooms).map(([room, count]) => ({ room, count }))
          : [];
      rooms.forEach((room) => {
        const name = room.room || room[0] || room.name;
        if (name) roomMap.set(name, room.count ?? roomMap.get(name) ?? 0);
      });
    });
    const current = ui.roomFilter.value.trim();
    ui.roomFilter.replaceChildren(new Option("All rooms", ""));
    [...roomMap.entries()].sort(([a], [b]) => a.localeCompare(b)).forEach(([name]) => {
      ui.roomFilter.add(new Option(name, name));
    });
    ui.roomFilter.value = current;
  }

  async function performSearch(event) {
    event.preventDefault();
    if (state.miningActive) return;
    const query = ui.searchQuery.value.trim();
    const params = new URLSearchParams();
    params.set("q", query);
    if (ui.wingFilter.value.trim()) params.set("wing", ui.wingFilter.value.trim());
    if (ui.roomFilter.value.trim()) params.set("room", ui.roomFilter.value.trim());
    const payload = await safeRequest([
      `/dashboard/search?${params.toString()}`,
      `/search?${params.toString()}`,
      `/api/dashboard/search?${params.toString()}`,
      `/api/search?${params.toString()}`,
    ]);
    const results = payload.results || payload.drawers || payload.items || payload || [];
    renderSearchResults(Array.isArray(results) ? results : []);
  }

  function bindEvents() {
    ui.savePrefs.addEventListener("click", async () => {
      savePrefs();
      if (hasToken()) {
        await bootstrap();
      }
    });

    ui.searchForm.addEventListener("submit", (event) => {
      performSearch(event).catch((error) => {
        ui.searchSummary.textContent = `Search failed: ${error.message}`;
        ui.searchResults.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
      });
    });

    ui.wingFilter.addEventListener("change", () => {
      if (state.miningActive) return;
      refreshDrawers().catch((error) => renderConnectionState(error.message, "error"));
    });

    ui.roomFilter.addEventListener("change", () => {
      if (state.miningActive) return;
      refreshDrawers().catch((error) => renderConnectionState(error.message, "error"));
    });
  }

  async function bootstrap() {
    const generation = ++state.bootstrapGeneration;
    state.baseUrl = normalizeBase(ui.apiBase.value);
    state.token = ui.tokenInput.value.trim();
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    if (!hasToken()) {
      renderDisconnectedState("Enter and save a bearer token to load dashboard data.");
      return;
    }
    try {
      await refreshOverview();
      if (generation !== state.bootstrapGeneration) {
        return;
      }
      let timerId = null;
      timerId = setInterval(() => {
        if (generation !== state.bootstrapGeneration) {
          clearInterval(timerId);
          if (state.pollTimer === timerId) {
            state.pollTimer = null;
          }
          return;
        }
        refreshOverview().catch((error) => renderConnectionState(error.message, "error"));
      }, 15000);
      state.pollTimer = timerId;
    } catch (error) {
      if (generation !== state.bootstrapGeneration) {
        return;
      }
      renderConnectionState(error.message, "error");
      ui.serviceHealth.textContent = "Offline";
      ui.miningState.textContent = "Unknown";
      ui.taxonomyStatus.textContent = "Unable to load authenticated backend telemetry.";
      ui.searchResults.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
      ui.drawerList.innerHTML = `<div class="empty-state status-bad">${escapeHtml(error.message)}</div>`;
    }
  }

  loadPrefs();
  bindEvents();
  bootstrap();
})();
