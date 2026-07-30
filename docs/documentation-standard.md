# Documentation standard

Every primary Python SDK guide must include its audience and prerequisites, an
OSS/Orkes capability label when behavior differs, and a security note when it
handles credentials, user data, tools, or external side effects.

Commands must be runnable or marked **Fragment** and linked to a complete
repository example. State the expected result, common failure modes, cleanup,
and next steps. Use `conductor-python` and published PyPI versions rather than
stale pinned versions. CI validates internal Markdown links and curated example
paths.
