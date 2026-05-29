-- ============================================================
-- JobPilot — Database Initialization
-- Creates the necessary extensions for PostgreSQL
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
