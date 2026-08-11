from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hatchet_sdk.contracts.dispatcher_pb2 import STEP_EVENT_TYPE_COMPLETED
from hatchet_sdk.runnables.action import ActionType
from hatchet_sdk.worker.action_listener_process import (
    ActionEvent,
    WorkerActionListenerProcess,
)


@pytest.mark.asyncio
async def test_send_event_retries_dispatch_failures() -> None:
    process = WorkerActionListenerProcess.__new__(WorkerActionListenerProcess)
    process.running_step_runs = {}
    process.dispatcher_client = MagicMock()
    process.dispatcher_client.send_step_action_event = AsyncMock(
        side_effect=[RuntimeError("connection closed"), None]
    )
    action = MagicMock(action_type=ActionType.START_STEP_RUN)
    event = ActionEvent(
        action=action,
        type=STEP_EVENT_TYPE_COMPLETED,
        payload=None,
        should_not_retry=False,
    )

    with patch(
        "hatchet_sdk.worker.action_listener_process.exp_backoff_sleep",
        new_callable=AsyncMock,
    ) as sleep:
        await process.send_event(event)

    assert process.dispatcher_client.send_step_action_event.await_count == 2
    sleep.assert_awaited_once_with(1, 1)


@pytest.mark.asyncio
async def test_send_event_does_not_retry_success() -> None:
    process = WorkerActionListenerProcess.__new__(WorkerActionListenerProcess)
    process.running_step_runs = {}
    process.dispatcher_client = MagicMock()
    process.dispatcher_client.send_step_action_event = AsyncMock(return_value=None)
    action = MagicMock(action_type=ActionType.START_STEP_RUN)
    event = ActionEvent(
        action=action,
        type=STEP_EVENT_TYPE_COMPLETED,
        payload=None,
        should_not_retry=False,
    )

    with patch(
        "hatchet_sdk.worker.action_listener_process.exp_backoff_sleep",
        new_callable=AsyncMock,
    ) as sleep:
        await process.send_event(event)

    process.dispatcher_client.send_step_action_event.assert_awaited_once_with(
        action,
        STEP_EVENT_TYPE_COMPLETED,
        None,
        False,
    )
    sleep.assert_not_awaited()
