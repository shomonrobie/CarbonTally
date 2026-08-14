CarbonTally Backend V2 - Final Implementation Instructions

Reference: CT-BV2-FINAL-001Status: APPROVED - FROZENAudience: Cline / AI Development Agents

These architecture decisions are mandatory implementation requirementsunless replaced by a newer approved Architecture Decision Record(ADR).

CT-ARCH-001 --- Backend Architecture

Decision

Supabase is the Backend-as-a-Service (BaaS).

FastAPI is the Business Processing Engine.

Rules

React communicates directly with Supabase for CRUD.

FastAPI must not duplicate CRUD endpoints.

Supabase provides Authentication, RLS, Storage and Realtime.

FastAPI accesses Supabase only when business processing requiresdatabase interaction.

CT-ARCH-002 --- CRUD Ownership

Supabase owns

Authentication

User management

Organizations

Facilities

Assets

Document metadata

Storage

Realtime

CRUD

Row Level Security

FastAPI owns

Business logic

Validation

Factor matching

Emission calculations

PDF/OCR processing

Excel/CSV processing

Report generation

Workflow orchestration

AI processing (future)

CT-ARCH-003 --- Backend Engines

Backend V2 shall be organised as independent engines.

Required:

FactorMatchingEngine

CalculationEngine

PDFExtractionEngine

ExcelImportEngine

CSVImportEngine

DocumentProcessingEngine

ReportGenerationEngine

ValidationEngine

WorkflowEngine

Future:

AIExtractionEngine

BenchmarkEngine

RecommendationEngine

CT-ARCH-004 --- Intelligent Factor Matching Engine

This is the primary intellectual property of CarbonTally.

The engine:

matches activities to emission factors

never performs calculations

never depends on PDF, Excel or CSV formats

only accepts standardized activity objects

CT-ARCH-005 --- Standard Activity Object

Every importer must transform its source into one common internal objectbefore matching.

Examples of sources:

Manual entry

PDF

OCR

Excel

CSV

API integrations

All become the same standardized activity object.

CT-ARCH-006 --- Matching Strategy

Matching priority:

Exact

Alias

Synonym

Hierarchical

Keyword

AI ranking (future)

Every response shall include:

matched factor

confidence score

matching method

warnings

The engine must never silently guess.

CT-ARCH-007 --- Multi-Provider Design

CarbonTally is NOT DEFRA-specific.

Target providers include:

DEFRA

Ireland

EU

IPCC

Custom organization libraries

Supporting a new provider should primarily require:

provider adapter

import mapping

configuration

No redesign of the matching engine.

CT-ARCH-008 --- Factor Libraries

The engine matches against libraries.

Examples:

DEFRA-2025

DEFRA-2026

IE-2025

EU-2026

Never hard-code DEFRA assumptions.

CT-ARCH-009 --- Platform Administration

Platform Admin shall include:

Factor Providers

Factor Libraries

Import Wizard

Import Validation

Alias Dictionary

Synonym Dictionary

Units

Countries

Reporting Years

Import History

Publish / Archive

CT-ARCH-010 --- Import Workflow

Upload

↓

Validate

↓

Preview

↓

Publish

↓

Rebuild Search Index

↓

Active Library

No imported data becomes active until published.

CT-ARCH-011 --- In-Memory Search Index

When Backend starts:

load active factor libraries

parse hierarchy

build searchable cache

rebuild after publishing new libraries

Use cache for matching instead of querying the database repeatedly.

CT-ARCH-012 --- Backend API Philosophy

Backend exposes ONLY business-processing endpoints.

Examples:

POST /process/pdf

POST /process/excel

POST /process/csv

POST /factor-match

POST /calculate

POST /generate-report

No CRUD endpoints.

CT-ARCH-013 --- Legacy Backend

Freeze current backend as backend_legacy.

Reuse business logic selectively.

Do NOT reuse the routing architecture.

CT-ARCH-014 --- Explainability

Every automatic match shall record:

factor_id

factor library

confidence

matching method

timestamp

All automated decisions must be explainable.

CT-ARCH-015 --- Extensibility

Adding a new country or factor provider should require importing andconfiguring a new factor library rather than rewriting applicationlogic.

CT-ARCH-016 --- Engine Independence

Each engine must be independently testable and reusable.

Dependencies:

DocumentProcessingEngine → FactorMatchingEngine → CalculationEngine →ReportGenerationEngine

Each engine has a single responsibility.

Implementation Notes for Cline

Treat RC2 as the authoritative database schema.

Build Backend V2 beside the legacy backend.

Implement engines first, endpoints second.

Prefer composition over large route files.

Keep business logic isolated from transport (HTTP) logic.

Ensure future support for UK, Ireland, EU and additional factorlibraries without architectural changes.

This document is the implementation blueprint for Backend V2.