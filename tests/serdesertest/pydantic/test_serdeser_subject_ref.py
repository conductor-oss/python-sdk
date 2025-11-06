
import json

import pytest
from pydantic import ValidationError

from conductor.client.adapters.models.subject_ref_adapter import SubjectRefAdapter
from tests.serdesertest.util.serdeser_json_resolver_utility import JsonTemplateResolver


@pytest.fixture
def raw_server_json():
    return JsonTemplateResolver.get_json_string("SubjectRef")


@pytest.fixture
def server_json(raw_server_json):
    return json.loads(raw_server_json)


def test_subject_ref_deserialization(raw_server_json, server_json):
    subject_ref_adapter = SubjectRefAdapter.from_json(raw_server_json)
    assert subject_ref_adapter.to_dict() == server_json


def test_subject_ref_serialization(raw_server_json, server_json):
    assert sorted(SubjectRefAdapter(**server_json).to_json()) == sorted(raw_server_json)


def test_subject_ref_invalid_data():
    with pytest.raises(ValidationError):
        SubjectRefAdapter(subject_id={"invalid_id"})
