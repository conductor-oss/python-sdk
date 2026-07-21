# Upgrade the Python SDK safely

Before upgrading, read the release notes, test against the target Conductor
server, and pin the new package version in a staging environment. Run unit tests
and one representative workflow and agent execution before production rollout.

The canonical agent configuration names use `CONDUCTOR_AGENT_*`. Legacy
configuration aliases continue to work for compatibility, but new deployments
should use the canonical names. Roll back by restoring the prior package lock and
keeping workflow definitions versioned rather than changing active behavior in place.
