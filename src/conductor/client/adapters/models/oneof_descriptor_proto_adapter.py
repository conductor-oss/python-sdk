from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.client.http.models import OneofDescriptorProto


class OneofDescriptorProtoAdapter(OneofDescriptorProto): ...
