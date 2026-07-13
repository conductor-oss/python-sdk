# Copyright (c) 2025 Agentspan
# Licensed under the MIT License. See LICENSE file in the project root for details.

"""The SDK must stamp a credential-requiring worker's declared secret names onto
TaskDef.runtimeMetadata at registration, so the host resolves them at poll time
and the SDK's overwrite-registration does not wipe the value."""

from conductor.ai.agents.runtime.runtime import (
    _credential_names,
    _default_task_def,
    _passthrough_task_def,
)


class TestCredentialNames:
    def test_extracts_string_names(self):
        assert _credential_names(["GH_TOKEN", "AWS_KEY"]) == ["GH_TOKEN", "AWS_KEY"]

    def test_dedups_preserving_order(self):
        assert _credential_names(["A", "B", "A"]) == ["A", "B"]

    def test_reads_name_attribute_and_ignores_junk(self):
        class Cred:
            def __init__(self, name):
                self.name = name

        assert _credential_names([Cred("X"), 42, None, "Y"]) == ["X", "Y"]

    def test_none_and_empty(self):
        assert _credential_names(None) == []
        assert _credential_names([]) == []


class TestTaskDefStamping:
    def test_default_task_def_stamps_runtime_metadata(self):
        td = _default_task_def("gh_tool", runtime_metadata=["GH_TOKEN"])
        assert td.runtime_metadata == ["GH_TOKEN"]

    def test_default_task_def_no_metadata_leaves_none(self):
        td = _default_task_def("plain_tool")
        assert not td.runtime_metadata  # None or empty — never a clobbering []

    def test_passthrough_task_def_stamps_runtime_metadata(self):
        td = _passthrough_task_def("fw_worker", runtime_metadata=["MY_SECRET"])
        assert td.runtime_metadata == ["MY_SECRET"]
