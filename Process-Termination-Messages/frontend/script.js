/* ============================================================
   Process Termination Messages — Dashboard Script
   Operating Systems and Systems Programming (25CS2104E)

   Polls GET /api/processes every 1 second.
   For RUNNING processes, remaining time is computed from:
       remaining = duration - elapsed_seconds_since_start_time
   This means the C program does NOT need to update the DB
   every second; the browser does the countdown locally.
   ============================================================ */

"use strict";

/* ---- Configuration ---- */
const POLL_INTERVAL_MS = 1000;   /* how often to fetch /api/processes */

/* ---- DOM References ---- */
const totalCountEl    = document.getElementById("total-count");
const runningCountEl  = document.getElementById("running-count");
const completedCountEl= document.getElementById("completed-count");
const liveStatusEl    = document.getElementById("live-status");
const lastUpdatedEl   = document.getElementById("last-updated");
const tbodyEl         = document.getElementById("process-tbody");

/* ---- State ---- */
let processData = [];   /* latest snapshot from the server */

/* ============================================================
   fetchProcesses()
   Calls the Flask API and stores the result in processData.
   ============================================================ */
async function fetchProcesses() {
    try {
        const response = await fetch("/api/processes");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        processData = data;
        liveStatusEl.textContent = "Live";
        liveStatusEl.style.color = "#68d391";

    } catch (err) {
        liveStatusEl.textContent = "Error";
        liveStatusEl.style.color = "#fc8181";
        console.error("Failed to fetch /api/processes:", err);
    }
}

/* ============================================================
   computeRemaining(process)

   For a RUNNING process:
       elapsed  = now - start_time (in seconds)
       remaining = duration - elapsed  (clamped to 0)

   For a COMPLETED process: return 0.
   ============================================================ */
function computeRemaining(proc) {
    if (proc.status === "COMPLETED") {
        return 0;
    }

    if (!proc.start_time) {
        return proc.duration;
    }

    const startMs  = new Date(proc.start_time).getTime();
    const nowMs    = Date.now();
    const elapsedS = (nowMs - startMs) / 1000;
    const remaining = proc.duration - elapsedS;

    return remaining < 0 ? 0 : remaining;
}

/* ============================================================
   formatTime(isoString)
   Formats an ISO datetime string as HH:MM:SS for the table.
   ============================================================ */
function formatTime(isoString) {
    if (!isoString) return "—";
    const d = new Date(isoString);
    return d.toLocaleTimeString();
}

/* ============================================================
   renderTable()
   Rebuilds the table body and summary cards from processData.
   Called every second so remaining times update smoothly.
   ============================================================ */
function renderTable() {
    if (processData.length === 0) {
        tbodyEl.innerHTML = `
            <tr>
                <td colspan="8" class="placeholder-msg">
                    No process data yet. Run the C process manager to begin.
                </td>
            </tr>`;
        totalCountEl.textContent     = "0";
        runningCountEl.textContent   = "0";
        completedCountEl.textContent = "0";
        return;
    }

    /* ---- Summary counts ---- */
    let running   = 0;
    let completed = 0;

    processData.forEach(p => {
        if (p.status === "RUNNING")    running++;
        if (p.status === "COMPLETED")  completed++;
    });

    totalCountEl.textContent     = processData.length;
    runningCountEl.textContent   = running;
    completedCountEl.textContent = completed;

    /* ---- Build table rows ---- */
    let html = "";

    processData.forEach(proc => {
        const isRunning   = proc.status === "RUNNING";
        const badge       = isRunning
            ? '<span class="badge badge-running">RUNNING</span>'
            : '<span class="badge badge-completed">COMPLETED</span>';

        const remaining   = computeRemaining(proc);
        const remainStr   = Math.ceil(remaining) + "s";
        const remainClass = isRunning ? "remaining-running" : "remaining-done";

        const startStr    = formatTime(proc.start_time);
        const endStr      = formatTime(proc.end_time);
        const message     = proc.termination_message
            ? proc.termination_message
            : '<span style="color:#4a5568;">—</span>';

        html += `
        <tr>
            <td>${proc.process_no}</td>
            <td><code>${proc.pid}</code></td>
            <td>${badge}</td>
            <td>${proc.duration}s</td>
            <td class="${remainClass}">${remainStr}</td>
            <td>${startStr}</td>
            <td>${endStr}</td>
            <td>${message}</td>
        </tr>`;
    });

    tbodyEl.innerHTML = html;

    /* ---- Last updated timestamp ---- */
    lastUpdatedEl.textContent = "Last updated: " + new Date().toLocaleTimeString();
}

/* ============================================================
   Main polling loop

   1. Fetch latest data from Flask every POLL_INTERVAL_MS.
   2. Render the table every POLL_INTERVAL_MS so remaining
      times count down smoothly even between fetches.
   ============================================================ */
async function tick() {
    await fetchProcesses();
    renderTable();
}

/* Render immediately on load, then every second */
tick();
setInterval(renderTable, POLL_INTERVAL_MS);

/* Fetch fresh data from Flask every second */
setInterval(fetchProcesses, POLL_INTERVAL_MS);
