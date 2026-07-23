"""Public compatibility tests for the Conductor-agent error rename."""

from conductor.ai.agents import AgentspanError, ConductorAgentError
from conductor.client.ai import AgentspanError as ClientLegacyError
from conductor.client.ai import ConductorAgentError as ClientError


def test_legacy_error_is_the_canonical_error_class():
    assert ConductorAgentError is AgentspanError
    assert ClientError is ClientLegacyError
    assert ClientError is ConductorAgentError
