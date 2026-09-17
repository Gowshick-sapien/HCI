"""
Benchmark test for Test Bench Suite WebSocket streaming latency (TBS-D2).
Asserts that network dispatch latency over loopback is under 10.0 ms (INV-TBS.3).
Strict Zero Emojis Policy Enforced.
"""

import asyncio
import json
import socket
import time
import pytest
import aiohttp

from src.testbench.server import TestbenchServer


def get_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestTestbenchLatencyBenchmark:
    """Evaluates WebSocket broadcast-to-receive transmission latency."""

    @pytest.mark.asyncio
    async def test_loopback_streaming_latency(self):
        """
        Transmits 60 consecutive perception packets and verifies that
        average dispatch latency over loopback is strictly below 10.0 ms.
        """
        port = get_free_port()
        server = TestbenchServer(host="127.0.0.1", port=port)
        server.start(blocking=False)

        ws_url = f"http://127.0.0.1:{port}/ws"
        latencies_ms = []

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                await asyncio.sleep(0.05)

                for i in range(60):
                    t_sent = time.perf_counter()
                    server.broadcast_perception(
                        gaze_x=500.0,
                        gaze_y=300.0,
                        active_mode="GESTURE",
                        gesture_token="PINCH_INDEX" if i % 10 == 0 else "NONE",
                        gesture_confidence=0.9,
                        command="PRIMARY_CLICK" if i % 10 == 0 else "NO_ACTION",
                        timestamp=t_sent,
                        gaze_fixated=True
                    )

                    msg = await asyncio.wait_for(ws.receive(), timeout=2.0)
                    t_recv = time.perf_counter()
                    assert msg.type == aiohttp.WSMsgType.TEXT

                    elapsed_ms = (t_recv - t_sent) * 1000.0
                    latencies_ms.append(elapsed_ms)

        server.stop()

        assert len(latencies_ms) == 60
        mean_latency = sum(latencies_ms) / len(latencies_ms)
        p95_latency = sorted(latencies_ms)[int(len(latencies_ms) * 0.95)]

        print(f"\n[LATENCY BENCHMARK] Mean: {mean_latency:.2f} ms, P95: {p95_latency:.2f} ms, Max: {max(latencies_ms):.2f} ms")

        # Invariant INV-TBS.3: WebSocket streaming latency < 10.0 ms
        assert mean_latency < 10.0, f"Mean latency {mean_latency:.2f} ms exceeds 10.0 ms threshold."
