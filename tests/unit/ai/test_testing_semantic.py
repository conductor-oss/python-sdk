"""Tests for conductor.ai.agents.testing.semantic."""

import os
import subprocess
import sys

# The import shown in semantic.py's own module docstring.  A failure here is a
# collection error, which is the point: the docstring must stay executable.
from conductor.ai.agents.testing import assert_output_satisfies
from conductor.ai.agents.testing.semantic import (
    assert_output_satisfies as assert_output_satisfies_direct,
)


def test_package_export_is_the_semantic_function():
    assert assert_output_satisfies is assert_output_satisfies_direct


def test_star_import_exposes_assert_output_satisfies():
    """`__all__` membership, asserted through what it actually governs."""
    namespace: dict = {}
    exec("from conductor.ai.agents.testing import *", namespace)  # noqa: S102

    assert namespace["assert_output_satisfies"] is assert_output_satisfies_direct


def test_importing_the_package_does_not_import_litellm():
    """Re-exporting semantic.py must not drag its optional dependency in.

    ``litellm`` is imported lazily inside ``assert_output_satisfies``.  If it
    ever moved to module scope, this package-level re-export would turn an
    optional dependency into a hard one for every importer of ``testing``.
    Run in a subprocess so an unrelated test cannot pre-populate sys.modules.
    """
    source = (
        "import sys\n"
        "import conductor.ai.agents.testing\n"
        "assert 'litellm' not in sys.modules, 'litellm imported eagerly'\n"
    )
    # The subprocess inherits neither pytest's pythonpath setting nor this
    # process's sys.path, so hand it the path `conductor` actually resolved
    # from -- otherwise it may import a different checkout.
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    subprocess.run([sys.executable, "-c", source], check=True, env=env)
