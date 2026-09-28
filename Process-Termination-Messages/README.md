# Process Termination Messages

**Course:** Operating Systems and Systems Programming (25CS2104E)

**Team:**
- K.V. Koushal
- Y. Charan Sai
- B. Shashank

---

## Project Purpose

This project demonstrates how a Linux parent process creates, manages, synchronizes with, and monitors **100+ real child processes** — simulating a simplified Linux Server Workload / Job Process Monitoring system.

A real Linux server handles many independent tasks concurrently: file processing, report generation, data processing, background jobs, and so on. In this project, each **child process** represents one such job. The **parent process** manages all jobs, synchronizes with their completion using `waitpid()`, and records their status. A **web dashboard** lets an administrator see which jobs are running, how much time remains, and the termination message of completed jobs.

> **Note:** This is a simplified educational model, not a replacement for production server monitoring software.

---

## Features

- **100+ real Linux child processes** created with `fork()`
- Concurrent execution — all children run simultaneously
- **Live web dashboard** that updates every second
- Remaining time countdown computed by the browser
- RUNNING → COMPLETED status transitions
- Termination messages for each process
- MySQL persistent storage
- Clean dark-themed UI (no frontend framework)

---

## Technologies Used

| Layer | Technology |
|-------|-----------|
| Process Management | C (Linux) |
| Backend | Python / Flask |
| Database | MySQL |
| Frontend | HTML + CSS + JavaScript |

---

## Architecture

```
C Process Manager  (fork / waitpid / sleep / exit)
        │
        │  writes events
        ▼
process_events.csv
        │
        │  Flask reads on each API call
        ▼
Flask Backend  (app.py)
        │
        │  INSERT / UPDATE
        ▼
MySQL Database  (process_monitor.processes)
        │
        │  JSON response to browser
        ▼
HTML / CSS / JavaScript Dashboard
```

---

## Folder Structure

```
Process-Termination-Messages/
├── c_program/
│   └── process_manager.c     ← Core OS program
│
├── backend/
│   ├── app.py                ← Flask backend
│   └── requirements.txt
│
├── frontend/
│   ├── index.html            ← Dashboard page
│   ├── style.css
│   └── script.js
│
├── database/
│   └── schema.sql            ← MySQL schema
│
├── docs/
│   └── REPORT.md             ← Full project report
│
├── screenshots/              ← Add screenshots here
│
├── process_events.csv        ← Generated at runtime by C program
├── README.md
└── .gitignore
```

---

## C Program — `c_program/process_manager.c`

### What it does

1. Opens `process_events.csv` and writes `RESET` (clears old run data).
2. Calls `fork()` **100 times** in a loop — creating 100 real Linux child processes.
3. Each child calls `sleep(duration)` then `exit(0)`.
4. The parent records each child's PID and writes a `CREATE` event immediately after each `fork()`.
5. After all children are created, the parent enters a `waitpid(-1, NULL, 0)` loop.
6. Each time `waitpid()` returns, the parent identifies which child finished (by searching `child_pids[]`), then writes a `COMPLETE` event.

### Process durations

```c
duration = (i % 5) + 1;   // gives 1, 2, 3, 4, 5, 1, 2, 3, 4, 5 ...
```

This ensures children finish at different times, making the live dashboard meaningful.

### Allowed functions

| Function | Purpose |
|----------|---------|
| `fork()` | Create child processes |
| `getpid()` | Obtain parent PID |
| `sleep()` | Simulate job execution |
| `exit()` | Child terminates cleanly |
| `waitpid()` | Parent synchronizes with child termination |
| `fopen/fprintf/fclose` | Write to event file |

---

## Event File — `process_events.csv`

The C parent writes events in this format:

```
RESET
CREATE,1,18001,1,
CREATE,2,18002,2,
CREATE,3,18003,3,
...
COMPLETE,1,18001,1,Process 1 terminated successfully
COMPLETE,2,18002,2,Process 2 terminated successfully
...
```

| Event | Fields |
|-------|--------|
| `RESET` | Signals Flask to clear old records |
| `CREATE` | `event_type, process_no, pid, duration, (empty message)` |
| `COMPLETE` | `event_type, process_no, pid, duration, termination_message` |

---

## Flask Backend — `backend/app.py`

- Serves the dashboard at `http://localhost:5000/`
- Exposes `GET /api/processes`
- On every API call: reads `process_events.csv`, syncs all events into MySQL, queries all rows, returns JSON
- No background threads; simple and explainable

### Configuration

Open `backend/app.py` and set your MySQL password:

```python
DB_HOST     = "localhost"
DB_USER     = "root"
DB_PASSWORD = "YOUR_PASSWORD"   # ← change this
DB_NAME     = "process_monitor"
```

---

## MySQL Database

**Database:** `process_monitor`  
**Table:** `processes`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT AUTO_INCREMENT | Primary key |
| `process_no` | INT UNIQUE | 1-based process number |
| `pid` | INT | Linux process ID |
| `status` | VARCHAR(20) | RUNNING or COMPLETED |
| `duration` | INT | Total sleep seconds |
| `start_time` | DATETIME | When CREATE was processed |
| `end_time` | DATETIME | When COMPLETE was processed |
| `termination_message` | VARCHAR(255) | Completion message |

---

## Frontend Dashboard

- Polls `GET /api/processes` every **1 second**
- Computes remaining time client-side: `remaining = duration − elapsed_since_start_time`
- Displays: Process No, PID, Status, Duration, Remaining, Start Time, End Time, Termination Message
- Status badges: 🟠 **RUNNING** / 🟢 **COMPLETED**
- No React, no Node.js, no frontend framework

---

## Installation & Setup

### Prerequisites

- **Linux / Ubuntu** (for the C program — WSL works on Windows)
- **Python 3.x**
- **MySQL Server**
- **GCC** compiler

---

### Step 1 — Start MySQL

```bash
sudo service mysql start
```

---

### Step 2 — Create the Database

```bash
mysql -u root -p < database/schema.sql
```

---

### Step 3 — Set Your MySQL Password

Edit `backend/app.py` and replace `YOUR_PASSWORD` with your MySQL root password.

---

### Step 4 — Install Python Requirements

```bash
pip install -r backend/requirements.txt
```

---

### Step 5 — Start the Flask Backend

```bash
python3 backend/app.py
```

Keep this terminal open. Flask will print:

```
  Dashboard : http://localhost:5000/
```

---

### Step 6 — Open the Dashboard

Open your browser and go to:

```
http://localhost:5000/
```

The dashboard will show "No process data yet" until you run the C program.

---

### Step 7 — Compile the C Program

Open a new terminal (on Linux/WSL):

```bash
cd c_program
gcc process_manager.c -o process_manager
```

---

### Step 8 — Run the C Program

```bash
./process_manager
```

You will see output like:

```
========================================
   PROCESS TERMINATION MESSAGES
========================================

Parent Process Started
Parent PID: 15000

Creating 100 child processes...

Process 1 created - PID: 15001 (duration: 1s)
Process 2 created - PID: 15002 (duration: 2s)
...
Process 100 created - PID: 15100 (duration: 5s)

All child processes created.
Parent waiting for child processes...

Process 1 terminated  (PID: 15001)
Process 6 terminated  (PID: 15006)
...

All child processes terminated.

========================================
          PROJECT COMPLETED
========================================
```

---

## Expected Dashboard Behaviour

1. The dashboard shows 100 rows.
2. All start as **RUNNING**.
3. Remaining time counts down for each process.
4. Short-duration processes (1s, 2s) complete first and turn **COMPLETED**.
5. Termination messages appear for completed processes.
6. Within ~5 seconds all 100 processes show **COMPLETED**.

---

## Changing the Number of Processes

In `c_program/process_manager.c`:

```c
#define TOTAL_PROCESSES 100   /* change to 150 or 200 */
```

Recompile and run again.

---

## Viva Preparation

| Question | Answer |
|----------|--------|
| Why C? | Core OS concepts (fork, waitpid, etc.) are implemented in C on Linux |
| Why Flask? | Lightweight Python backend to bridge the event file, MySQL, and the dashboard |
| Why 100 processes? | To demonstrate process management at scale, not just a single child |
| Why waitpid()? | To synchronize parent with child termination and identify which child finished |
| Why not signals? | The project focuses on fork/waitpid synchronization; signals are out of scope |
| Why CSV? | Simple bridge between C and Python without sockets or networking |

---

## License

This project is submitted as a B.Tech academic project for the course Operating Systems and Systems Programming (25CS2104E).
