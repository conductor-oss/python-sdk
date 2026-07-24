"""Public export tests for the Conductor Agents error hierarchy."""

from conductor.ai.agents import ConductorAgentError
from conductor.client.ai import ConductorAgentError as ClientError


def test_conductor_agent_error_is_the_canonical_error_class():
    assert ClientError is ConductorAgentError
