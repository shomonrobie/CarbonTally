"""CarbonTally business-processing engines (Backend v2.1 §7).

Engines implement the platform's business processing. Each engine has a single
responsibility, is stateless (a new instance per request) and depends only on
``core``, ``domain``, ``infra`` and the repository layer — never on the API
layer, and never on other engines except through constructor injection
(§4.2).

Phase 4 ships the Factor Matching Engine and its six pipeline stages.
"""
from __future__ import annotations

from engines.ai_extraction import DEFAULT_FIELDS, AIExtractionEngine
from engines.benchmarking import BenchmarkingEngine
from engines.calculation import (
    DEFAULT_ALGORITHM_VERSION,
    CalculationEngine,
    CalculationRequest,
    CalculationSink,
)
from engines.extraction import DocumentExtractionEngine, DocumentSink
from engines.factor_matching import FactorMatchingEngine, build_matching_pipeline
from engines.workflow import WorkflowOrchestrator, WorkflowResult
from engines.matching_stages import (
    AliasMatchStage,
    AliasResolver,
    ExactMatchStage,
    FuzzyMatchStage,
    KeywordSearchStage,
    NaturalKeyStage,
    RepositoryAliasResolver,
    SemanticMatchStage,
    SemanticScorer,
)
from engines.validation import ValidationEngine
from engines.report_generation import (
    ReportContent,
    ReportGenerationEngine,
    ReportGenerationResult,
)

__all__ = [
    "AIExtractionEngine",
    "AliasMatchStage",
    "AliasResolver",
    "BenchmarkingEngine",
    "CalculationEngine",
    "CalculationRequest",
    "CalculationSink",
    "DEFAULT_ALGORITHM_VERSION",
    "DEFAULT_FIELDS",
    "DocumentExtractionEngine",
    "DocumentSink",
    "ExactMatchStage",
    "FactorMatchingEngine",
    "FuzzyMatchStage",
    "KeywordSearchStage",
    "NaturalKeyStage",
    "RepositoryAliasResolver",
    "ReportContent",
    "ReportGenerationEngine",
    "ReportGenerationResult",
    "SemanticMatchStage",
    "SemanticScorer",
    "ValidationEngine",
    "WorkflowOrchestrator",
    "WorkflowResult",
    "build_matching_pipeline",
]


