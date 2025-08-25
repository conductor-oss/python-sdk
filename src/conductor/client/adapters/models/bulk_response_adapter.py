from __future__ import annotations

from conductor.client.http.models import BulkResponse


class BulkResponseAdapter(BulkResponse):
    def __init__(
        self, bulk_error_results=None, bulk_successful_results=None, *_args, **_kwargs
    ):
        super().__init__(
            bulk_error_results=bulk_error_results,
            bulk_successful_results=bulk_successful_results,
        )
