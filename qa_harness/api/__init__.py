"""API QA module: OpenAPI discovery, contract checks, authorization
(allow/deny framework), security boundaries and workflow state machines."""

from qa_harness.api.inventory import ApiEndpoint, EndpointInventory
from qa_harness.api.authorization import AuthorizationExpectation, AuthorizationMatrix
from qa_harness.api.contract import ContractCheck
from qa_harness.api.workflows import StateTransition, WorkflowStateMachine

__all__ = [
    "ApiEndpoint",
    "AuthorizationExpectation",
    "AuthorizationMatrix",
    "ContractCheck",
    "EndpointInventory",
    "StateTransition",
    "WorkflowStateMachine",
]
