"""
Integration test for Multimodal Test Bench Suite Pipeline (TBS-D2).
Verifies end-to-end integration across perception frame generation, WebSocket streaming,
frontend message parsing, and feedback recording.
Strict Zero Emojis Policy Enforced.
"""

import asyncio
import json
import socket
import time
import pytest
import aiohttp

from src.storage.schemas import (
    ActionType,
    DeviceMode,
    GestureToken,
)
from src.testbench.server import TestbenchServer


def get_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestTestbenchPipelineIntegration:
    """End-to-end integration tests for the testbench streaming pipeline."""

    @pytest.mark.asyncio
    async def test_end_to_end_perception_streaming(self):
        """
        Verifies that synthesized perception frames correctly broadcast
        over WebSocket, preserve precision coordinates, and process returned interaction events.
        """
        port = get_free_port()
        server = TestbenchServer(host="127.0.0.1", port=port)
        server.start(blocking=False)

        recorded_events = []
        server.register_callback(lambda evt: recorded_events.append(evt))

        ws_url = f"http://127.0.0.1:{port}/ws"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                await asyncio.sleep(0.05)

                # Simulate sequence of 5 perception frames
                for i in range(5):
                    target_x = 300.0 + i * 20.0
                    target_y = 250.0 + i * 15.0
                    server.broadcast_perception(
                        gaze_x=target_x,
                        gaze_y=target_y,
                        active_mode="GESTURE",
                        gesture_token="PINCH_INDEX" if i == 4 else "NONE",
                        gesture_confidence=0.95 if i == 4 else 0.0,
                        command="PRIMARY_CLICK" if i == 4 else "NO_ACTION",
                        timestamp=time.time(),
                        gaze_fixated=True
                    )

                    msg = await asyncio.wait_for(ws.receive(), timeout=2.0)
                    assert msg.type == aiohttp.WSMsgType.TEXT
                    packet = json.loads(msg.data)
                    assert packet["type"] == "PERCEPTION_UPDATE"
                    assert packet["gaze_x"] == target_x
                    assert packet["gaze_y"] == target_y

                # Trigger interaction event response from client (simulating user click on TB-T01)
                client_feedback = {
                    "type": "INTERACTION_EVENT",
                    "target_id": "TB-T01",
                    "action_type": "PRIMARY_CLICK",
                    "is_successful": True,
                    "timestamp": time.time()
                }
                await ws.send_str(json.dumps(client_feedback))
                await asyncio.sleep(0.05)

                # Verify server received and recorded event
                assert len(server.received_events) == 1
                assert server.received_events[0]["target_id"] == "TB-T01"
                assert len(recorded_events) == 1
                assert recorded_events[0]["is_successful"] is True

        server.stop()
        assert not server.is_running
