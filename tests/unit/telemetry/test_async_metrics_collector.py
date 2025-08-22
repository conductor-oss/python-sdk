import asyncio
import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import Counter, Gauge

from conductor.asyncio_client.telemetry.metrics_collector import AsyncMetricsCollector
from conductor.shared.telemetry.configuration.metrics import MetricsSettings
from conductor.shared.telemetry.enums import MetricDocumentation, MetricLabel, MetricName


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def metrics_settings():
    return MetricsSettings(directory="/tmp/test_metrics", file_name="test.log", update_interval=0.1)


@pytest.fixture
def metrics_collector(metrics_settings):
    return AsyncMetricsCollector(metrics_settings)


@pytest.fixture
def mock_counter():
    counter = MagicMock(spec=Counter)
    counter.labels.return_value.inc = MagicMock()
    return counter


@pytest.fixture
def mock_gauge():
    gauge = MagicMock(spec=Gauge)
    gauge.labels.return_value.set = MagicMock()
    return gauge


@pytest.mark.asyncio
async def test_init_with_settings(metrics_settings):
    with patch.dict('os.environ', {}, clear=True), \
         patch('prometheus_client.multiprocess.MultiProcessCollector') as mock_collector:
        collector = AsyncMetricsCollector(metrics_settings)
        
        assert collector.must_collect_metrics is True
        assert collector.settings == metrics_settings
        assert os.environ["PROMETHEUS_MULTIPROC_DIR"] == "/tmp/test_metrics"


@pytest.mark.asyncio
async def test_init_without_settings():
    collector = AsyncMetricsCollector(None)
    assert collector.must_collect_metrics is False


@pytest.mark.asyncio
async def test_provide_metrics_success(metrics_settings):
    with patch('os.path.join', return_value="/tmp/test_metrics/test.log"), \
         patch('os.environ.get', return_value="/tmp/test_metrics"), \
         patch('os.path.isdir', return_value=True), \
         patch('prometheus_client.multiprocess.MultiProcessCollector'), \
         patch('prometheus_client.write_to_textfile') as mock_write, \
         patch('asyncio.sleep') as mock_sleep:
        
        mock_sleep.side_effect = asyncio.CancelledError()
        
        with pytest.raises(asyncio.CancelledError):
            await AsyncMetricsCollector.provide_metrics(metrics_settings)


@pytest.mark.asyncio
async def test_provide_metrics_with_none_settings():
    result = await AsyncMetricsCollector.provide_metrics(None)
    assert result is None


@pytest.mark.asyncio
async def test_provide_metrics_error_handling(metrics_settings):
    with patch('os.path.join', return_value="/tmp/test_metrics/test.log"), \
         patch('os.environ.get', return_value="/tmp/test_metrics"), \
         patch('os.path.isdir', return_value=True), \
         patch('prometheus_client.multiprocess.MultiProcessCollector'), \
         patch('prometheus_client.write_to_textfile', side_effect=Exception("Write failed")), \
         patch('asyncio.sleep') as mock_sleep:
        
        mock_sleep.side_effect = asyncio.CancelledError()
        
        with pytest.raises(asyncio.CancelledError):
            await AsyncMetricsCollector.provide_metrics(metrics_settings)


@pytest.mark.asyncio
async def test_increment_task_poll(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_poll("test_task")
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_POLL
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_POLL
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_counter.labels.assert_called_once_with("test_task")
        mock_counter.labels.return_value.inc.assert_called_once()


@pytest.mark.asyncio
async def test_increment_task_execution_queue_full(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_execution_queue_full("test_task")
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_EXECUTION_QUEUE_FULL
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_EXECUTION_QUEUE_FULL
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_counter.labels.assert_called_once_with("test_task")


@pytest.mark.asyncio
async def test_increment_uncaught_exception(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_uncaught_exception()
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.THREAD_UNCAUGHT_EXCEPTION
        assert call_args[1]['documentation'] == MetricDocumentation.THREAD_UNCAUGHT_EXCEPTION
        assert list(call_args[1]['labelnames']) == []
        mock_counter.labels.assert_called_once_with()


@pytest.mark.asyncio
async def test_increment_task_poll_error(metrics_collector, mock_counter):
    exception = Exception("Test error")
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_poll_error("test_task", exception)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_POLL_ERROR
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_POLL_ERROR
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE, MetricLabel.EXCEPTION]
        mock_counter.labels.assert_called_once_with("test_task", "Test error")


@pytest.mark.asyncio
async def test_increment_task_paused(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_paused("test_task")
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_PAUSED
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_PAUSED
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_counter.labels.assert_called_once_with("test_task")


@pytest.mark.asyncio
async def test_increment_task_execution_error(metrics_collector, mock_counter):
    exception = Exception("Execution error")
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_execution_error("test_task", exception)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_EXECUTE_ERROR
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_EXECUTE_ERROR
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE, MetricLabel.EXCEPTION]
        mock_counter.labels.assert_called_once_with("test_task", "Execution error")


@pytest.mark.asyncio
async def test_increment_task_ack_failed(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_ack_failed("test_task")
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_ACK_FAILED
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_ACK_FAILED
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_counter.labels.assert_called_once_with("test_task")


@pytest.mark.asyncio
async def test_increment_task_ack_error(metrics_collector, mock_counter):
    exception = Exception("ACK error")
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_ack_error("test_task", exception)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_ACK_ERROR
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_ACK_ERROR
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE, MetricLabel.EXCEPTION]
        mock_counter.labels.assert_called_once_with("test_task", "ACK error")


@pytest.mark.asyncio
async def test_increment_task_update_error(metrics_collector, mock_counter):
    exception = Exception("Update error")
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_update_error("test_task", exception)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.TASK_UPDATE_ERROR
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_UPDATE_ERROR
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE, MetricLabel.EXCEPTION]
        mock_counter.labels.assert_called_once_with("test_task", "Update error")


@pytest.mark.asyncio
async def test_increment_external_payload_used(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_external_payload_used("entity", "operation", "type")
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.EXTERNAL_PAYLOAD_USED
        assert call_args[1]['documentation'] == MetricDocumentation.EXTERNAL_PAYLOAD_USED
        assert list(call_args[1]['labelnames']) == [MetricLabel.ENTITY_NAME, MetricLabel.OPERATION, MetricLabel.PAYLOAD_TYPE]
        mock_counter.labels.assert_called_once_with("entity", "operation", "type")


@pytest.mark.asyncio
async def test_increment_workflow_start_error(metrics_collector, mock_counter):
    exception = Exception("Workflow error")
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_workflow_start_error("workflow_type", exception)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_counter.call_args
        assert call_args[1]['name'] == MetricName.WORKFLOW_START_ERROR
        assert call_args[1]['documentation'] == MetricDocumentation.WORKFLOW_START_ERROR
        assert list(call_args[1]['labelnames']) == [MetricLabel.WORKFLOW_TYPE, MetricLabel.EXCEPTION]
        mock_counter.labels.assert_called_once_with("workflow_type", "Workflow error")


@pytest.mark.asyncio
async def test_record_workflow_input_payload_size(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_workflow_input_payload_size("workflow_type", "v1", 1024)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_gauge.call_args
        assert call_args[1]['name'] == MetricName.WORKFLOW_INPUT_SIZE
        assert call_args[1]['documentation'] == MetricDocumentation.WORKFLOW_INPUT_SIZE
        assert list(call_args[1]['labelnames']) == [MetricLabel.WORKFLOW_TYPE, MetricLabel.WORKFLOW_VERSION]
        mock_gauge.labels.assert_called_once_with("workflow_type", "v1")
        mock_gauge.labels.return_value.set.assert_called_once_with(1024)


@pytest.mark.asyncio
async def test_record_task_result_payload_size(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_task_result_payload_size("test_task", 512)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_gauge.call_args
        assert call_args[1]['name'] == MetricName.TASK_RESULT_SIZE
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_RESULT_SIZE
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_gauge.labels.assert_called_once_with("test_task")
        mock_gauge.labels.return_value.set.assert_called_once_with(512)


@pytest.mark.asyncio
async def test_record_task_poll_time(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_task_poll_time("test_task", 1.5)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_gauge.call_args
        assert call_args[1]['name'] == MetricName.TASK_POLL_TIME
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_POLL_TIME
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_gauge.labels.assert_called_once_with("test_task")
        mock_gauge.labels.return_value.set.assert_called_once_with(1.5)


@pytest.mark.asyncio
async def test_record_task_execute_time(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_task_execute_time("test_task", 2.3)
        
        call_args = metrics_collector._AsyncMetricsCollector__get_gauge.call_args
        assert call_args[1]['name'] == MetricName.TASK_EXECUTE_TIME
        assert call_args[1]['documentation'] == MetricDocumentation.TASK_EXECUTE_TIME
        assert list(call_args[1]['labelnames']) == [MetricLabel.TASK_TYPE]
        mock_gauge.labels.assert_called_once_with("test_task")
        mock_gauge.labels.return_value.set.assert_called_once_with(2.3)


@pytest.mark.asyncio
async def test_increment_counter_disabled_metrics():
    collector = AsyncMetricsCollector(None)
    with patch.object(collector, '_AsyncMetricsCollector__get_counter') as mock_get_counter:
        await collector.increment_task_poll("test_task")
        mock_get_counter.assert_not_called()


@pytest.mark.asyncio
async def test_record_gauge_disabled_metrics():
    collector = AsyncMetricsCollector(None)
    with patch.object(collector, '_AsyncMetricsCollector__get_gauge') as mock_get_gauge:
        await collector.record_task_execute_time("test_task", 1.0)
        mock_get_gauge.assert_not_called()


@pytest.mark.asyncio
async def test_get_counter_existing(metrics_collector):
    existing_counter = MagicMock(spec=Counter)
    metrics_collector.counters[MetricName.TASK_POLL] = existing_counter
    
    result = await metrics_collector._AsyncMetricsCollector__get_counter(
        MetricName.TASK_POLL, MetricDocumentation.TASK_POLL, [MetricLabel.TASK_TYPE]
    )
    
    assert result == existing_counter


@pytest.mark.asyncio
async def test_get_gauge_existing(metrics_collector):
    existing_gauge = MagicMock(spec=Gauge)
    metrics_collector.gauges[MetricName.TASK_EXECUTE_TIME] = existing_gauge
    
    result = await metrics_collector._AsyncMetricsCollector__get_gauge(
        MetricName.TASK_EXECUTE_TIME, MetricDocumentation.TASK_EXECUTE_TIME, [MetricLabel.TASK_TYPE]
    )
    
    assert result == existing_gauge


@pytest.mark.asyncio
async def test_generate_counter(metrics_collector):
    result = await metrics_collector._AsyncMetricsCollector__generate_counter(
        MetricName.TASK_POLL, MetricDocumentation.TASK_POLL, [MetricLabel.TASK_TYPE]
    )
    
    assert isinstance(result, Counter)
    assert result._name == MetricName.TASK_POLL
    assert result._documentation == MetricDocumentation.TASK_POLL


@pytest.mark.asyncio
async def test_generate_gauge(metrics_collector):
    result = await metrics_collector._AsyncMetricsCollector__generate_gauge(
        MetricName.TASK_EXECUTE_TIME, MetricDocumentation.TASK_EXECUTE_TIME, [MetricLabel.TASK_TYPE]
    )
    
    assert isinstance(result, Gauge)
    assert result._name == MetricName.TASK_EXECUTE_TIME
    assert result._documentation == MetricDocumentation.TASK_EXECUTE_TIME


@pytest.mark.asyncio
async def test_increment_counter_with_complex_exception(metrics_collector, mock_counter):
    exception = ValueError("Complex error with special chars: !@#$%^&*()")
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_poll_error("test_task", exception)
        
        mock_counter.labels.assert_called_once_with("test_task", "Complex error with special chars: !@#$%^&*()")


@pytest.mark.asyncio
async def test_record_gauge_with_zero_value(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_task_execute_time("test_task", 0.0)
        
        mock_gauge.labels.return_value.set.assert_called_once_with(0.0)


@pytest.mark.asyncio
async def test_record_gauge_with_negative_value(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_task_execute_time("test_task", -1.5)
        
        mock_gauge.labels.return_value.set.assert_called_once_with(-1.5)


@pytest.mark.asyncio
async def test_increment_counter_with_empty_task_type(metrics_collector, mock_counter):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_counter', return_value=mock_counter):
        await metrics_collector.increment_task_poll("")
        
        mock_counter.labels.assert_called_once_with("")


@pytest.mark.asyncio
async def test_record_gauge_with_large_payload_size(metrics_collector, mock_gauge):
    with patch.object(metrics_collector, '_AsyncMetricsCollector__get_gauge', return_value=mock_gauge):
        await metrics_collector.record_task_result_payload_size("test_task", 999999999)
        
        mock_gauge.labels.return_value.set.assert_called_once_with(999999999) 