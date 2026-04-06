"""Custom exceptions for the application.

This module defines custom exception types for specific error conditions
that can occur during routing, execution, and service operations.
"""


class MotherbrainException(Exception):
    """Base exception for all Motherbrain errors."""
    pass


# Routing Exceptions
class NoAgentAvailable(MotherbrainException):
    """Raised when no agent is available for a job.
    
    This occurs when all agents are offline or no agent has the
    required capabilities for the job.
    """
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"No agent available for job {job_id}")


class NoMCPServiceAvailable(MotherbrainException):
    """Raised when no MCP service is available for a job.
    
    This occurs when all MCP services are offline or no service has the
    required capabilities for the job.
    """
    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"No MCP service available for job {job_id}")


# MCP Service Exceptions
class MCPServiceTimeout(MotherbrainException):
    """Raised when an MCP service call times out."""
    def __init__(self, service_id: str):
        self.service_id = service_id
        super().__init__(f"MCP service {service_id} timed out")


class MCPServiceError(MotherbrainException):
    """Raised when an MCP service returns an error."""
    def __init__(self, service_id: str, details: str):
        self.service_id = service_id
        self.details = details
        super().__init__(f"MCP service {service_id} error: {details}")


class MCPServiceNotFound(MotherbrainException):
    """Raised when an MCP service is not found."""
    def __init__(self, service_id: str):
        self.service_id = service_id
        super().__init__(f"MCP service {service_id} not found")
