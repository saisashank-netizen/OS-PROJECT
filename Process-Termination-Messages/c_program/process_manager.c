/*
 * ============================================================
 *  PROCESS TERMINATION MESSAGES
 *  Operating Systems and Systems Programming (25CS2104E)
 *
 *  Team:
 *    K.V. KOUSHAL
 *    Y. CHARAN SAI
 *    B. SHASHANK
 *
 *  File   : process_manager.c
 *  Purpose: Create and manage 100+ real Linux child processes.
 *           Each child simulates an independent server job.
 *           The parent synchronizes with all children using
 *           waitpid() and writes process events to a CSV file.
 * ============================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <time.h>

/* -------------------------------------------------------
 * Configuration
 * Change TOTAL_PROCESSES to 100, 150, or 200 as needed.
 * ------------------------------------------------------- */
#define TOTAL_PROCESSES 100

/* Path to the event file read by the Flask backend */
#define EVENT_FILE "../process_events.csv"

/* -------------------------------------------------------
 * write_create_event()
 *
 * Writes a CREATE line to the event file for a child that
 * has just been forked.
 *
 *   fp         - open file pointer (append mode)
 *   process_no - 1-based process number
 *   pid        - child PID returned by fork()
 *   duration   - seconds the child will sleep
 * ------------------------------------------------------- */
void write_create_event(FILE *fp, int process_no, pid_t pid, int duration)
{
    fprintf(fp, "CREATE,%d,%d,%d,\n", process_no, (int)pid, duration);
    fflush(fp);
}

/* -------------------------------------------------------
 * write_complete_event()
 *
 * Writes a COMPLETE line to the event file after waitpid()
 * returns the child's PID.
 *
 *   fp         - open file pointer (append mode)
 *   process_no - 1-based process number
 *   pid        - child PID
 *   duration   - the original duration of this child
 * ------------------------------------------------------- */
void write_complete_event(FILE *fp, int process_no, pid_t pid, int duration)
{
    fprintf(fp, "COMPLETE,%d,%d,%d,Process %d terminated successfully\n",
            process_no, (int)pid, duration, process_no);
    fflush(fp);
}

/* -------------------------------------------------------
 * main()
 * ------------------------------------------------------- */
int main(void)
{
    pid_t  child_pids[TOTAL_PROCESSES];   /* store child PIDs           */
    int    durations[TOTAL_PROCESSES];    /* store each child's duration */
    int    i;
    pid_t  parent_pid;
    FILE  *fp;

    /* ---- Banner ---- */
    printf("========================================\n");
    printf("   PROCESS TERMINATION MESSAGES\n");
    printf("========================================\n\n");

    parent_pid = getpid();
    printf("Parent Process Started\n");
    printf("Parent PID: %d\n\n", (int)parent_pid);

    /* ---- Open / reset event file ---- */
    fp = fopen(EVENT_FILE, "w");
    if (fp == NULL)
    {
        perror("fopen (event file)");
        return 1;
    }

    /* Write RESET so Flask clears old records before new run */
    fprintf(fp, "RESET\n");
    fflush(fp);

    /* ---- Create all child processes first ---- */
    printf("Creating %d child processes...\n\n", TOTAL_PROCESSES);

    for (i = 0; i < TOTAL_PROCESSES; i++)
    {
        pid_t pid;
        int   duration;

        /*
         * Assign varying durations: 1, 2, 3, 4, 5, 1, 2, ...
         * This ensures children finish at different times so
         * the dashboard shows meaningful live updates.
         */
        duration = (i % 5) + 1;
        durations[i] = duration;

        pid = fork();

        if (pid < 0)
        {
            /* fork() failed – print error and continue */
            perror("fork");
            child_pids[i] = -1;
            continue;
        }

        if (pid == 0)
        {
            /* ---- CHILD PROCESS ----
             * Each child represents one server job.
             * It sleeps to simulate job execution time,
             * then exits cleanly.
             */
            sleep(duration);
            exit(0);
        }

        /* ---- PARENT continues here ---- */
        child_pids[i] = pid;

        /* Record the CREATE event immediately */
        write_create_event(fp, i + 1, pid, duration);

        printf("Process %d created - PID: %d (duration: %ds)\n",
               i + 1, (int)pid, duration);
    }

    printf("\nAll child processes created.\n");
    printf("Parent waiting for child processes...\n\n");

    /* ---- Wait for all children to terminate ---- */
    /*
     * waitpid(-1, NULL, 0) blocks until ANY child terminates.
     * The returned PID is used to identify which child finished.
     * We search child_pids[] to find the matching process number.
     */
    {
        int completed = 0;

        while (completed < TOTAL_PROCESSES)
        {
            pid_t finished_pid;
            int   j;

            finished_pid = waitpid(-1, NULL, 0);

            if (finished_pid <= 0)
            {
                /* No more children or error */
                break;
            }

            /* Find which process number corresponds to this PID */
            for (j = 0; j < TOTAL_PROCESSES; j++)
            {
                if (child_pids[j] == finished_pid)
                {
                    /* Write COMPLETE event */
                    write_complete_event(fp, j + 1, finished_pid, durations[j]);

                    printf("Process %d terminated  (PID: %d)\n",
                           j + 1, (int)finished_pid);

                    /* Mark as handled so we don't match again */
                    child_pids[j] = -1;
                    completed++;
                    break;
                }
            }
        }
    }

    fclose(fp);

    printf("\nAll child processes terminated.\n\n");
    printf("========================================\n");
    printf("          PROJECT COMPLETED\n");
    printf("========================================\n");

    return 0;
}
