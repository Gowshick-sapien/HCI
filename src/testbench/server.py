"""
Test Bench Suite (TBS-D2) Bidirectional Streaming Server.
Provides asynchronous HTTP and WebSocket bridge between the multimodal
perception pipeline and the browser-based interactive testbench.
Zero Emojis across the entire scope.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set

from aiohttp import web, WSMsgType

logger = logging.getLogger(__name__)


class TestbenchServer:
    """
    Asynchronous HTTP and WebSocket streaming bridge for the Multimodal Test Bench Suite.
    Serves static testbench frontend assets and handles bidirectional 60 FPS perception telemetry.
    """
    __test__ = False

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        frontend_dir: Optional[Path | str] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.frontend_dir = (
            Path(frontend_dir)
            if frontend_dir is not None
            else Path(__file__).resolve().parent / "frontend"
        )
        self._clients: Set[web.WebSocketResponse] = set()
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._received_events: List[Dict[str, Any]] = []

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Returns True if the server is active and listening."""
        return self._is_running

    @property
    def client_count(self) -> int:
        """Returns the number of connected WebSocket clients."""
        with self._lock:
            return len(self._clients)

    @property
    def received_events(self) -> List[Dict[str, Any]]:
        """Returns a copy of recorded client interaction events."""
        with self._lock:
            return list(self._received_events)

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Registers a listener for client interaction events."""
        with self._lock:
            self._callbacks.append(callback)

    def clear_events(self) -> None:
        """Clears accumulated interaction events."""
        with self._lock:
            self._received_events.clear()

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serves the index.html landing page."""
        index_file = self.frontend_dir / "index.html"
        if not index_file.exists():
            return web.Response(status=404, text="Testbench frontend index.html not found.")
        return web.FileResponse(index_file)

    async def _handle_gestures(self, request: web.Request) -> web.Response:
        """Serves the gestures.html standalone gesture vocabulary testing page."""
        gestures_file = self.frontend_dir / "gestures.html"
        if not gestures_file.exists():
            return web.Response(status=404, text="Testbench frontend gestures.html not found.")
        return web.FileResponse(gestures_file)

    async def _handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        """Handles WebSocket connections for real-time perception streaming and event reporting."""
        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)

        with self._lock:
            self._clients.add(ws)
        logger.info("Testbench WebSocket client connected. Active clients: %d", self.client_count)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if isinstance(data, dict):
                            with self._lock:
                                self._received_events.append(data)
                                callbacks = list(self._callbacks)
                            for cb in callbacks:
                                try:
                                    cb(data)
                                except Exception as cb_err:
                                    logger.error("Error executing testbench event callback: %s", cb_err)
                    except json.JSONDecodeError as err:
                        logger.warning("Invalid JSON received from testbench client: %s", err)
                elif msg.type in (WSMsgType.CLOSED, WSMsgType.ERROR):
                    break
        finally:
            with self._lock:
                self._clients.discard(ws)
            logger.info("Testbench WebSocket client disconnected. Remaining clients: %d", self.client_count)

        return ws

    def _build_app(self) -> web.Application:
        """Configures the aiohttp application with routes and static asset handlers."""
        app = web.Application()
        app.router.add_get("/", self._handle_index)
        app.router.add_get("/gestures", self._handle_gestures)
        app.router.add_get("/gestures.html", self._handle_gestures)
        app.router.add_get("/ws", self._handle_ws)
        if self.frontend_dir.exists():
            app.router.add_static("/", path=self.frontend_dir, show_index=False)
        return app

    def start(self, blocking: bool = False) -> None:
        """
        Starts the HTTP and WebSocket server.
        If blocking is True, runs synchronously on the calling thread.
        If False, runs on a dedicated background daemon thread.
        """
        if self._is_running:
            return

        ready_event = threading.Event()

        def _run() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            app = self._build_app()
            self._runner = web.AppRunner(app)
            self._loop.run_until_complete(self._runner.setup())
            self._site = web.TCPSite(self._runner, self.host, self.port)
            self._loop.run_until_complete(self._site.start())
            self._is_running = True
            ready_event.set()
            logger.info("Testbench server listening on http://%s:%d", self.host, self.port)
            try:
                self._loop.run_forever()
            finally:
                if self._runner is not None:
                    self._loop.run_until_complete(self._runner.cleanup())
                self._loop.close()
                self._is_running = False

        if blocking:
            _run()
        else:
            self._thread = threading.Thread(target=_run, name="TestbenchServerThread", daemon=True)
            self._thread.start()
            if not ready_event.wait(timeout=5.0):
                raise TimeoutError("TestbenchServer failed to initialize within 5.0 seconds.")

    def stop(self) -> None:
        """Gracefully stops the server and closes all active client connections."""
        if not self._is_running or self._loop is None:
            return

        async def _shutdown() -> None:
            with self._lock:
                clients = list(self._clients)
            for ws in clients:
                await ws.close(code=1000, message=b"Server shutting down")
            if self._site is not None:
                await self._site.stop()
            if self._runner is not None:
                await self._runner.cleanup()

        try:
            future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
            future.result(timeout=3.0)
        except Exception as err:
            logger.warning("Warning during testbench server shutdown: %s", err)
        finally:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=3.0)
            self._is_running = False
            logger.info("Testbench server stopped successfully.")

    def broadcast_packet(self, packet: Dict[str, Any]) -> None:
        """
        Threadsafe broadcast of a dictionary packet to all connected clients.
        Encodes as JSON and posts asynchronously via the event loop.
        """
        if not self._is_running or self._loop is None:
            return

        with self._lock:
            clients = list(self._clients)

        if not clients:
            return

        payload = json.dumps(packet)

        async def _broadcast() -> None:
            coros = [ws.send_str(payload) for ws in clients if not ws.closed]
            if coros:
                await asyncio.gather(*coros, return_exceptions=True)

        asyncio.run_coroutine_threadsafe(_broadcast(), self._loop)

    def broadcast_perception(
        self,
        gaze_x: float,
        gaze_y: float,
        active_mode: str = "GESTURE",
        gesture_token: str = "NONE",
        gesture_confidence: float = 0.0,
        command: str = "NO_ACTION",
        timestamp: Optional[float] = None,
        gaze_fixated: bool = False,
        norm_gaze_x: Optional[float] = None,
        norm_gaze_y: Optional[float] = None,
    ) -> None:
        """Constructs and broadcasts a standard PERCEPTION_UPDATE packet."""
        nx = float(norm_gaze_x) if norm_gaze_x is not None else float(gaze_x / 1920.0)
        ny = float(norm_gaze_y) if norm_gaze_y is not None else float(gaze_y / 1080.0)
        packet = {
            "type": "PERCEPTION_UPDATE",
            "timestamp": timestamp if timestamp is not None else time.time(),
            "gaze_x": float(gaze_x),
            "gaze_y": float(gaze_y),
            "norm_gaze_x": nx,
            "norm_gaze_y": ny,
            "gaze_fixated": bool(gaze_fixated),
            "active_mode": str(active_mode),
            "gesture_token": str(gesture_token),
            "gesture_confidence": float(gesture_confidence),
            "command": str(command),
        }
        self.broadcast_packet(packet)
