"""
Async Task Resource API - Provides async versions of task-related API endpoints.

This module contains async versions of the TaskResourceApi methods needed by AsyncTaskRunner.
Only batch_poll and update_task are implemented as these are the only methods needed
for async worker execution.
"""

import six

from conductor.client.http.async_api_client import AsyncApiClient


class AsyncTaskResourceApi(object):
    """Async Task Resource API for polling and updating tasks."""

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = AsyncApiClient()
        self.api_client = api_client

    async def batch_poll(self, tasktype, **kwargs):
        """Batch poll for tasks of a certain type (async version).

        This method makes an asynchronous HTTP request.

        :param str tasktype: (required) Task type to poll for
        :param str workerid: Worker ID
        :param str domain: Task domain
        :param int count: Number of tasks to poll
        :param int timeout: Poll timeout in milliseconds
        :return: list[Task]
        """
        kwargs['_return_http_data_only'] = True
        return await self.batch_poll_with_http_info(tasktype, **kwargs)

    async def batch_poll_with_http_info(self, tasktype, **kwargs):
        """Batch poll for a task of a certain type (async version).

        :param str tasktype: (required)
        :param str workerid: Worker ID
        :param str domain: Task domain
        :param int count: Number of tasks to poll
        :param int timeout: Poll timeout in milliseconds
        :return: list[Task]
        """

        all_params = ['tasktype', 'workerid', 'domain', 'count', 'timeout']
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method batch_poll" % key
                )
            params[key] = val
        del params['kwargs']

        # verify the required parameter 'tasktype' is set
        if ('tasktype' not in params or
                params['tasktype'] is None):
            raise ValueError("Missing the required parameter `tasktype` when calling `batch_poll`")

        collection_formats = {}

        path_params = {}
        if 'tasktype' in params:
            path_params['tasktype'] = params['tasktype']

        query_params = []
        if 'workerid' in params:
            query_params.append(('workerid', params['workerid']))
        if 'domain' in params:
            query_params.append(('domain', params['domain']))
        if 'count' in params:
            query_params.append(('count', params['count']))
        if 'timeout' in params:
            query_params.append(('timeout', params['timeout']))

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['*/*'])

        # Authentication setting
        auth_settings = []

        return await self.api_client.call_api(
            '/tasks/poll/batch/{tasktype}', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='list[Task]',
            auth_settings=auth_settings,
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    async def update_task(self, body, **kwargs):
        """Update a task (async version).

        This method makes an asynchronous HTTP request.

        :param TaskResult body: (required) Task result to update
        :return: str
        """
        kwargs['_return_http_data_only'] = True
        return await self.update_task_with_http_info(body, **kwargs)

    async def update_task_with_http_info(self, body, **kwargs):
        """Update a task (async version).

        :param TaskResult body: (required)
        :return: str
        """

        all_params = ['body']
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method update_task" % key
                )
            params[key] = val
        del params['kwargs']

        # verify the required parameter 'body' is set
        if ('body' not in params or
                params['body'] is None):
            raise ValueError("Missing the required parameter `body` when calling `update_task`")

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}

        body_params = None
        if 'body' in params:
            body_params = params['body']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['text/plain'])

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(
            ['application/json'])

        # Authentication setting
        auth_settings = []

        return await self.api_client.call_api(
            '/tasks', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='str',
            auth_settings=auth_settings,
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)
