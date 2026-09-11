"""Executable workflow definitions per persona/domain.

Each module defines the steps a future QA run will drive (customer, consultant,
client, PE, operations, admin, messaging). Steps declare expected statuses and
require persisted-state verification — never UI animations.
"""

from qa_harness.workflows.customer import CustomerWorkflow
from qa_harness.workflows.consultant import ConsultantWorkflow
from qa_harness.workflows.client import ClientWorkflow
from qa_harness.workflows.pe import ProcessingEntityWorkflow
from qa_harness.workflows.operations import OperationsWorkflow
from qa_harness.workflows.admin import AdminWorkflow
from qa_harness.workflows.messaging import MessagingWorkflow

ALL_WORKFLOWS = [
    CustomerWorkflow,
    ConsultantWorkflow,
    ClientWorkflow,
    ProcessingEntityWorkflow,
    OperationsWorkflow,
    AdminWorkflow,
    MessagingWorkflow,
]

__all__ = [
    "ALL_WORKFLOWS",
    "AdminWorkflow",
    "ClientWorkflow",
    "ConsultantWorkflow",
    "CustomerWorkflow",
    "MessagingWorkflow",
    "OperationsWorkflow",
    "ProcessingEntityWorkflow",
]
