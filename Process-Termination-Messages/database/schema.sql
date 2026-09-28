-- ============================================================
--  PROCESS TERMINATION MESSAGES
--  Database Schema
--  Operating Systems and Systems Programming (25CS2104E)
--
--  Run this file once to set up the database:
--    mysql -u root -p < database/schema.sql
-- ============================================================

-- Create the database if it does not already exist
CREATE DATABASE IF NOT EXISTS process_monitor;

USE process_monitor;

-- -------------------------------------------------------
-- Table: processes
--
-- Each row represents one real Linux child process.
--
-- Columns:
--   id                  - auto-increment primary key
--   process_no          - 1-based process number (unique per run)
--   pid                 - Linux process ID assigned by the OS
--   status              - RUNNING or COMPLETED
--   duration            - total sleep duration in seconds
--   start_time          - when the CREATE event was processed
--   end_time            - when the COMPLETE event was processed (NULL if still running)
--   termination_message - message written by the parent on completion
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS processes (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    process_no          INT          UNIQUE NOT NULL,
    pid                 INT          NOT NULL,
    status              VARCHAR(20)  NOT NULL,
    duration            INT          NOT NULL,
    start_time          DATETIME,
    end_time            DATETIME,
    termination_message VARCHAR(255)
);
