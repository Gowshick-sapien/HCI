"""
Unit tests for TestbenchServer (TBS-D2).
Verifies HTTP serving, WebSocket streaming, packet broadcasting, and event callbacks.
Strict Zero Emojis Policy Enforced.
"""

import asyncio
import json
import socket
import urllib.request
import pytest
import aiohttp

from src.testbench.server import TestbenchServer


def get_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestTestbenchServerUnit:
    """Unit test suite for the TestbenchServer streaming bridge."""

    def test_server_lifecycle_and_http_serving(self):
        """Verifies server start, static HTTP route serving, and stop."""
        port = get_free_port()
        server = TestbenchServer(host="127.0.0.1", port=port)
        assert not server.is_running

        server.start(blocking=False)
        assert server.is_running

        # Test HTTP GET index.html
        url = f"http://127.0.0.1:{port}/"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "Multimodal HCI Interactive Testbench Suite" in content

        # Test HTTP GET gestures.html
        gestures_url = f"http://127.0.0.1:{port}/gestures"
        req_gestures = urllib.request.Request(gestures_url)
        with urllib.request.urlopen(req_gestures, timeout=3.0) as resp:
            assert resp.status == 200
            gestures_content = resp.read().decode("utf-8")
            assert "Multimodal Gesture Vocabulary Suite" in gestures_content
            assert "PINCH_INDEX" in gestures_content
            assert "SWIPE_UP" in gestures_content

        # Test HTTP GET testbench.css
        css_url = f"http://127.0.0.1:{port}/testbench.css"
        with urllib.request.urlopen(css_url, timeout=3.0) as resp:
            assert resp.status == 200
            css_content = resp.read().decode("utf-8")
            assert "hitbox" in css_content.lower() or "reticle" in css_content.lower()

        server.stop()
        assert not server.is_running

    @pytest.mark.asyncio
    async def test_websocket_broadcast_and_client_events(self):
        """Verifies WebSocket client connection, perception frame broadcast, and client event callbacks."""
        port = get_free_port()
        server = TestbenchServer(host="127.0.0.1", port=port)
        server.start(blocking=False)

        received_callback_events = []

        def on_event(event_data):
            received_callback_events.append(event_data)

        server.register_callback(on_event)

        ws_url = f"http://127.0.0.1:{port}/ws"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                # Wait for connection to register on server
                await asyncio.sleep(0.1)
                assert server.client_count == 1

                # Broadcast perception frame from server
                server.broadcast_perception(
                    gaze_x=450.0,
                    gaze_y=320.0,
                    active_mode="GESTURE",
                    gesture_token="PINCH_INDEX",
                    gesture_confidence=0.92,
                    command="PRIMARY_CLICK",
                    gaze_fixated=True
                )

                # Client receives broadcast packet
                msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                assert msg.type == aiohttp.WSMsgType.TEXT
                data = json.loads(msg.data)
                assert data["type"] == "PERCEPTION_UPDATE"
                assert data["gaze_x"] == 450.0
                assert data["gaze_y"] == 320.0
                assert data["command"] == "PRIMARY_CLICK"
                assert data["gesture_token"] == "PINCH_INDEX"
                assert data["gaze_fixated"] is True

                # Client sends interaction feedback event
                event_payload = {
                    "type": "INTERACTION_EVENT",
                    "target_id": "TB-T01",
                    "action_type": "PRIMARY_CLICK",
                    "is_successful": True,
                    "timestamp": 1700000000.0
                }
                await ws.send_str(json.dumps(event_payload))
                await asyncio.sleep(0.1)

                # Assert server captured event
                assert len(server.received_events) == 1
                assert server.received_events[0]["target_id"] == "TB-T01"
                assert len(received_callback_events) == 1
                assert received_callback_events[0]["action_type"] == "PRIMARY_CLICK"

        await asyncio.sleep(0.1)
        server.stop()
        assert not server.is_running
