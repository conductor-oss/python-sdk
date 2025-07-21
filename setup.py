import setuptools
import os

version = os.environ["CONDUCTOR_PYTHON_VERSION"]
if version is None:
    version = "0.0.0-SNAPSHOT"

setuptools.setup(
    version=version,
)
