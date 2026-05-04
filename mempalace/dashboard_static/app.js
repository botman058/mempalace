(() => {
  const STORAGE_KEY = "mempalace.dashboard.prefs";
  const DEFAULT_BASE = "";

  const state = {
    baseUrl: DEFAULT_BASE,
    token: "",
    miningActive: false,
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
    if (!state.miningActive) {
      await Promise.allSettled([refreshTaxonomy(), refreshDrawers()]);
    } else {
      renderTaxonomy([]);
      renderDrawers([]);
    }
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
