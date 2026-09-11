"""Optional AI analysis layer (spec §27).

Deterministic tests always run; AI agents only analyze deterministic findings
— they never replace them. Without ``OPENROUTER_AGEN_SWARM_V1_API_KEY`` the
swarm reports ``SKIPPED — TOOL UNAVAILABLE``. No API key is hard-coded.
"""

from qa_harness.agents.swarm import AgentSwarm, openrouter_available

__all__ = ["AgentSwarm", "openrouter_available"]
