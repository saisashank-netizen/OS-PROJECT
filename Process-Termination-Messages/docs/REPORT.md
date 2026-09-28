# Process Termination Messages — Project Report

**Course:** Operating Systems and Systems Programming (25CS2104E)  
**Team:** K.V. Koushal &nbsp;|&nbsp; Y. Charan Sai &nbsp;|&nbsp; B. Shashank

---

## 1. Title

**Process Termination Messages**  
*Linux Server Workload / Job Process Monitoring*

---

## 2. Abstract

This project implements a simplified Linux Server Workload / Job Process Monitoring system as part of the Operating Systems and Systems Programming course. The core of the project is a C program that uses `fork()`, `waitpid()`, `sleep()`, `exit()`, and `getpid()` to create and manage over 100 real Linux child processes. Each child process simulates an independent server job. The parent process synchronizes with all child processes using `waitpid()` and writes process events to a CSV file. A Python Flask backend reads the event file, stores process information in a MySQL database, and exposes an API. A plain HTML/CSS/JavaScript dashboard polls the API every second and dynamically displays the running status, remaining time, and termination messages for all processes.

---

## 3. Introduction

Process management is a fundamental concept in operating systems. The operating system kernel creates and manages processes, schedules their execution, and handles their termination. At the application level, C programs on Linux can directly interact with OS process management features through system calls such as `fork()`, `waitpid()`, and `exit()`.

This project provides a practical, hands-on demonstration of these concepts at a scale larger than a trivial single-child example. By creating 100+ real child processes, the project illustrates how a parent process can manage a workload, synchronize with multiple concurrent processes, and record their termination.

To make the demonstration meaningful and visually interactive, the project adds a Flask backend and a web dashboard that display the live state of all processes in real time.

---

## 4. Problem Statement

Design and implement a Linux process monitoring system that:

- Creates 100 or more real Linux child processes using `fork()`.
- Allows child processes to execute concurrently.
- Synchronizes with their completion using `waitpid()`.
- Records process events (creation and termination) to a persistent file.
- Stores process information in a MySQL database.
- Displays a live web dashboard showing the status, remaining time, and termination message for each process.

---

## 5. Objectives

1. Demonstrate the use of `fork()` to create multiple real Linux child processes.
2. Demonstrate parent-child process relationships.
3. Demonstrate concurrent process execution.
4. Demonstrate process synchronization using `waitpid()`.
5. Demonstrate process termination using `exit()`.
6. Record process events to a CSV event file from the parent process.
7. Use a Flask backend to read events and store them in MySQL.
8. Build a live web dashboard to visualize the process monitoring data.

---

## 6. Practical Application

The practical application is:

**"Simplified Linux Server Workload / Job Process Monitoring"**

A production Linux server may handle many independent tasks concurrently: file processing, report generation, data import jobs, backup tasks, and other background operations. Each independent task can be modeled as a separate process. A process manager (the parent) creates these task processes, monitors them, and records their completion.

This project models that scenario in a simplified educational way:

- Each **child process** represents one server job.
- The **parent process** is the job manager.
- The **dashboard** is the administrator's monitoring interface.

**This is an educational simulation. It is not intended as a replacement for production monitoring tools such as systemd, supervisor, or monitoring software.**

---

## 7. System Architecture

```
┌──────────────────────────────────────┐
│       C Process Manager              │
│  (process_manager.c on Linux)        │
│                                      │
│  fork() × 100    → Child Processes   │
│  waitpid(-1,...) → Sync termination  │
│  fprintf(...)    → Write events      │
└───────────────┬──────────────────────┘
                │ writes
                ▼
        process_events.csv
                │ Flask reads on each API call
                ▼
┌───────────────────────────────────┐
│        Flask Backend              │
│  (backend/app.py)                 │
│                                   │
│  GET /api/processes               │
│  sync events → MySQL              │
│  return JSON                      │
└───────────────┬───────────────────┘
                │ SQL INSERT / UPDATE
                ▼
┌───────────────────────────────────┐
│        MySQL Database             │
│  database: process_monitor        │
│  table: processes                 │
│  (100 rows, one per child)        │
└───────────────┬───────────────────┘
                │ JSON response
                ▼
┌───────────────────────────────────┐
│   HTML / CSS / JavaScript         │
│   Dashboard (frontend/)           │
│                                   │
│   Polls /api/processes every 1s   │
│   Computes remaining time         │
│   Displays RUNNING / COMPLETED    │
└───────────────────────────────────┘
```

---

## 8. Methodology

The project was developed in four phases:

1. **C Program:** Implement process creation and synchronization using only the permitted OS functions.
2. **Event File:** Define a simple CSV format for communicating between the C program and the Python backend.
3. **Flask Backend and MySQL:** Implement event synchronization and the API.
4. **Frontend Dashboard:** Implement the live monitoring dashboard using plain HTML/CSS/JavaScript.

The components were tested together by running the C program and observing the dashboard.

---

## 9. Operating System Concepts

### 9.1 Process Creation — `fork()`

`fork()` is the standard UNIX system call for creating a new process. When called, the operating system creates an exact copy (child) of the calling process (parent). After `fork()`:

- In the **parent**: `fork()` returns the PID of the new child.
- In the **child**: `fork()` returns `0`.

This distinction is used in the C program to separate the parent's logic from the child's logic:

```c
pid = fork();
if (pid == 0) {
    /* child code */
    sleep(duration);
    exit(0);
}
/* parent code continues */
child_pids[i] = pid;
```

### 9.2 Parent-Child Relationship

The parent process is the process that calls `fork()`. The child process is a new process created by the kernel as a result of that call. The child inherits the parent's address space, file descriptors, and other attributes. The parent keeps track of child PIDs using an array:

```c
pid_t child_pids[TOTAL_PROCESSES];
```

### 9.3 Process Synchronization — `waitpid()`

After all children are created, the parent must synchronize with their termination. Without `waitpid()`, terminated children become **zombie processes** because their exit status remains in the process table until the parent collects it.

The parent uses:

```c
pid_t finished_pid = waitpid(-1, NULL, 0);
```

- `-1` means: wait for any child.
- `NULL` means: we do not need the exit status.
- `0` means: block until a child terminates.

The returned `finished_pid` is used to identify which child has completed by searching `child_pids[]`.

### 9.4 Process Termination — `exit()`

Each child terminates by calling:

```c
exit(0);
```

`exit(0)` performs cleanup (flushing I/O buffers, closing file descriptors) and then calls the `_exit()` system call, which terminates the process and signals the kernel that the process has finished. The exit status `0` conventionally means success.

### 9.5 Getting Process IDs — `getpid()`

The parent displays its own PID using:

```c
parent_pid = getpid();
printf("Parent PID: %d\n", (int)parent_pid);
```

Each child's PID is obtained from the return value of `fork()` in the parent.

---

## 10. Process Creation — Design

All 100 children are created **before** the parent waits for any of them. This is critical for demonstrating concurrent execution:

```
for i = 0 to 99:
    fork()
    record child PID
    write CREATE event

/* All 100 children now exist and are running concurrently */

while children remain:
    waitpid(-1, ...)
    identify child
    write COMPLETE event
```

If the parent were to `waitpid()` immediately after each `fork()`, only one child would exist at a time and the execution would be sequential — defeating the purpose of the demonstration.

---

## 11. Backend — Flask and MySQL

### Flask (`backend/app.py`)

Flask serves two roles:

1. Serves the frontend dashboard at `http://localhost:5000/`.
2. Exposes `GET /api/processes` which reads the event file, syncs events to MySQL, and returns JSON.

The event synchronization logic processes the CSV in order:

- `RESET` → `DELETE FROM processes`
- `CREATE` → `INSERT ... ON DUPLICATE KEY UPDATE` with `status = 'RUNNING'`
- `COMPLETE` → `UPDATE processes SET status = 'COMPLETED', end_time = ..., termination_message = ...`

### MySQL (`database/schema.sql`)

A single table `processes` stores one row per child process:

```sql
CREATE TABLE processes (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    process_no          INT UNIQUE NOT NULL,
    pid                 INT NOT NULL,
    status              VARCHAR(20) NOT NULL,
    duration            INT NOT NULL,
    start_time          DATETIME,
    end_time            DATETIME,
    termination_message VARCHAR(255)
);
```

---

## 12. Frontend — Dashboard

The dashboard (`frontend/`) is built with plain HTML, CSS, and JavaScript.

- **Polling:** `fetch("/api/processes")` is called every second.
- **Remaining time:** Computed by the browser from `start_time + duration`, not from the database, so the C program does not need to update records every second.
- **Status badges:** RUNNING (orange) and COMPLETED (green) are visually distinguished.
- **Summary cards:** Show total, running, and completed process counts.

---

## 13. Implementation Details

### Event File Format

```
RESET
CREATE,1,18001,1,
CREATE,2,18002,2,
...
COMPLETE,1,18001,1,Process 1 terminated successfully
COMPLETE,2,18002,2,Process 2 terminated successfully
...
```

The `RESET` line at the beginning ensures that when the C program is run again, the old process records are cleared from MySQL before new records are inserted.

### Duration Assignment

```c
duration = (i % 5) + 1;
```

This assigns durations 1, 2, 3, 4, 5 seconds cycling through all 100 processes. As a result:
- 20 processes complete after 1 second.
- 20 processes complete after 2 seconds.
- 20 processes complete after 3 seconds.
- 20 processes complete after 4 seconds.
- 20 processes complete after 5 seconds.

This gives the dashboard meaningful live updates over the 5-second execution window.

---

## 14. Testing

The following aspects were verified:

| Test | Expected Result |
|------|----------------|
| C program compiles with `gcc` | No errors or warnings |
| 100 child processes created | 100 CREATE lines in event file |
| All PIDs are different | Verified from terminal output |
| Children have different durations | 1s through 5s cycling |
| Parent waits for all children | 100 COMPLETE lines written |
| Flask starts without errors | Listening on port 5000 |
| MySQL connection works | No connection error on API call |
| Dashboard loads | HTML renders correctly at localhost:5000 |
| 100 rows appear in dashboard | Table shows all processes |
| RUNNING badges appear | Initial state all RUNNING |
| Remaining time counts down | Visible countdown in Remaining column |
| COMPLETED status appears | After child exits |
| Termination messages appear | "Process N terminated successfully" |

---

## 15. Results

- The C program successfully creates 100 real Linux child processes.
- All child processes run concurrently during the first 1–5 seconds.
- The parent correctly identifies each terminated child using `waitpid()`.
- The event file is correctly written and read by Flask.
- MySQL stores all 100 process records.
- The dashboard dynamically displays live status updates without requiring a manual page refresh.
- The project runs completely on a standard Linux/Ubuntu system with no special configuration beyond MySQL setup.

---

## 16. Advantages

- **Educational clarity:** Every component is simple and directly maps to an OS concept.
- **Real processes:** Uses actual Linux child processes, not simulations.
- **No overengineering:** No signals, threads, sockets, or complex libraries.
- **Viva-ready:** Every design decision can be explained simply.
- **Live visualization:** The dashboard makes process lifecycle visible in real time.

---

## 17. Limitations

- The project runs only on Linux (or WSL on Windows) because it relies on UNIX process system calls.
- The event file is re-read entirely on each API call. For 100–200 events this is fast, but it would not scale to millions of processes.
- The remaining time calculation uses the Flask server's time for `start_time`, which may slightly differ from the actual child process start time.
- The system does not handle the case where the C program is run multiple times simultaneously.

---

## 18. Future Scope

- Support multiple simultaneous runs by adding a session ID to the event file and database.
- Add a process priority or job type field to simulate different kinds of server jobs.
- Add a graph showing process completion over time.
- Extend to use named pipes (FIFOs) for real-time event delivery.
- Deploy the Flask backend as a proper Linux service using systemd.

---

## 19. Conclusion

This project successfully demonstrates the core operating system concepts of process creation, concurrent execution, parent-child relationships, and process synchronization using standard Linux system calls. The C program creates 100 real child processes and synchronizes with their termination using `waitpid()`. The Flask backend and MySQL database provide persistent storage, and the web dashboard provides a live, dynamic view of the process monitoring data.

The project is simple enough to be understood and defended in a viva examination, yet complete enough to demonstrate a full stack from OS-level process management through to a web-based monitoring interface.

---

*Report prepared for Operating Systems and Systems Programming (25CS2104E).*  
*K.V. Koushal | Y. Charan Sai | B. Shashank*
