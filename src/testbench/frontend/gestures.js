/**
 * Multimodal Gesture Vocabulary Verification Suite (TBS-G1)
 * Standalone Gesture Testing Matrix Controller
 * Strictly Zero Emojis Across Entire Scope
 */

(function () {
  "use strict";

  // Telemetry DOM Elements
  const elStatusConn = document.getElementById("status-connection");
  const elStatusModality = document.getElementById("status-modality");
  const elStatusGaze = document.getElementById("status-gaze");
  const elStatusGesture = document.getElementById("status-gesture");
  const elStatusAction = document.getElementById("status-action");
  const elStatusLatency = document.getElementById("status-latency");
  const btnRecenter = document.getElementById("btn-recenter-gaze");
  const btnResetAll = document.getElementById("btn-reset-all-gestures");

  // Live Gaze Reticle Canvas
  const canvasReticle = document.getElementById("gaze-reticle-canvas");
  const ctxReticle = canvasReticle ? canvasReticle.getContext("2d") : null;

  // Runtime Coordinates
  let currentGazeX = window.innerWidth / 2.0;
  let currentGazeY = window.innerHeight / 2.0;
  let targetGazeX = window.innerWidth / 2.0;
  let targetGazeY = window.innerHeight / 2.0;
  let rawGazeX = window.innerWidth / 2.0;
  let rawGazeY = window.innerHeight / 2.0;
  let gazeOffsetX = 0.0;
  let gazeOffsetY = 0.0;

  let activeModality = "GESTURE";
  let lastGestureToken = "NONE";
  let prevGestureToken = "NONE";
  let lastSocketTimestamp = performance.now();
  let socket = null;

  // 13 Vocabulary Tokens Definition
  const VOCABULARY_TOKENS = [
    "PINCH_INDEX",
    "PINCH_MIDDLE",
    "PINCH_RING",
    "PINCH_PINKY",
    "PINCH_HOLD",
    "PINCH_RELEASE",
    "SWIPE_LEFT",
    "SWIPE_RIGHT",
    "SWIPE_UP",
    "SWIPE_DOWN",
    "OPEN_PALM",
    "FIST",
    "THUMBS_UP"
  ];

  // Per-gesture metrics store
  const gestureMetrics = {};
  VOCABULARY_TOKENS.forEach(token => {
    gestureMetrics[token] = {
      count: 0,
      confidence: 0.0,
      activeTimer: null
    };
  });

  // Carousel indices for swipe demonstrations
  let leftCarouselIdx = 0;
  let rightCarouselIdx = 0;

  // Canvas Viewport Resize
  function resizeCanvas() {
    if (!canvasReticle) return;
    canvasReticle.width = window.innerWidth;
    canvasReticle.height = window.innerHeight;
  }
  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  // Recenter gaze reticle
  function recenterGaze() {
    gazeOffsetX = (window.innerWidth / 2.0) - rawGazeX;
    gazeOffsetY = (window.innerHeight / 2.0) - rawGazeY;
    targetGazeX = window.innerWidth / 2.0;
    targetGazeY = window.innerHeight / 2.0;
    currentGazeX = window.innerWidth / 2.0;
    currentGazeY = window.innerHeight / 2.0;
  }

  if (btnRecenter) {
    btnRecenter.addEventListener("click", recenterGaze);
  }

  window.addEventListener("keydown", function (e) {
    if (e.key === "c" || e.key === "C") {
      recenterGaze();
    }
  });

  // Render Reticle Loop (Smooth Lerp + Subtle Styling)
  function renderGazeReticle() {
    if (!ctxReticle || !canvasReticle) return;
    ctxReticle.clearRect(0, 0, canvasReticle.width, canvasReticle.height);

    // Smooth exponential lerp with saccade-snap threshold
    const dx = targetGazeX - currentGazeX;
    const dy = targetGazeY - currentGazeY;
    const dist = Math.hypot(dx, dy);

    if (dist > 200) {
      // Saccade detected: snap immediately with zero lag
      currentGazeX = targetGazeX;
      currentGazeY = targetGazeY;
    } else if (dist > 0.5) {
      // Exponential interpolation for butter-smooth fixation
      currentGazeX += dx * 0.30;
      currentGazeY += dy * 0.30;
    }

    if (activeModality !== "MOUSE_PRIORITY") {
      ctxReticle.save();

      // Subtle outer ring
      ctxReticle.beginPath();
      ctxReticle.arc(currentGazeX, currentGazeY, 16, 0, 2 * Math.PI);
      ctxReticle.strokeStyle = "rgba(56, 189, 248, 0.65)";
      ctxReticle.lineWidth = 1.5;
      ctxReticle.stroke();

      // Center dot
      ctxReticle.beginPath();
      ctxReticle.arc(currentGazeX, currentGazeY, 2.5, 0, 2 * Math.PI);
      ctxReticle.fillStyle = "rgba(56, 189, 248, 0.9)";
      ctxReticle.fill();

      // Hairline crosshairs
      ctxReticle.beginPath();
      ctxReticle.moveTo(currentGazeX - 22, currentGazeY);
      ctxReticle.lineTo(currentGazeX - 16, currentGazeY);
      ctxReticle.moveTo(currentGazeX + 16, currentGazeY);
      ctxReticle.lineTo(currentGazeX + 22, currentGazeY);
      ctxReticle.moveTo(currentGazeX, currentGazeY - 22);
      ctxReticle.lineTo(currentGazeX, currentGazeY - 16);
      ctxReticle.moveTo(currentGazeX + 16, currentGazeY);
      ctxReticle.lineTo(currentGazeX + 22, currentGazeY);
      ctxReticle.strokeStyle = "rgba(56, 189, 248, 0.5)";
      ctxReticle.lineWidth = 1;
      ctxReticle.stroke();

      ctxReticle.restore();
    }

    requestAnimationFrame(renderGazeReticle);
  }
  requestAnimationFrame(renderGazeReticle);

  // Convert token name to DOM element id fragment (e.g. PINCH_INDEX -> pinch-index)
  function tokenToId(token) {
    return token.toLowerCase().replace(/_/g, "-");
  }

  // Handle incoming perception packet
  function handlePerceptionUpdate(data) {
    const hasUsableGaze = data.gaze_confidence === undefined || data.gaze_confidence > 0.05;
    if (hasUsableGaze && data.norm_gaze_x !== undefined && data.norm_gaze_y !== undefined) {
      rawGazeX = data.norm_gaze_x * window.innerWidth;
      rawGazeY = data.norm_gaze_y * window.innerHeight;
    } else if (hasUsableGaze && data.gaze_x !== undefined && data.gaze_y !== undefined) {
      rawGazeX = (data.gaze_x / 1920.0) * window.innerWidth;
      rawGazeY = (data.gaze_y / 1080.0) * window.innerHeight;
    }

    targetGazeX = Math.max(0, Math.min(window.innerWidth, rawGazeX + gazeOffsetX));
    targetGazeY = Math.max(0, Math.min(window.innerHeight, rawGazeY + gazeOffsetY));

    activeModality = data.active_mode || "GESTURE";
    const token = data.gesture_token || "NONE";
    const confidence = parseFloat(data.gesture_confidence || 0.0);
    const command = data.command || "NO_ACTION";

    // Update Telemetry Header
    elStatusModality.textContent = activeModality;
    elStatusGaze.textContent = `(${Math.round(currentGazeX)}, ${Math.round(currentGazeY)})`;
    elStatusGesture.textContent = `${token} (${confidence.toFixed(2)})`;
    elStatusAction.textContent = command;

    const latency = (performance.now() - lastSocketTimestamp).toFixed(1);
    elStatusLatency.textContent = `${latency} ms`;
    lastSocketTimestamp = performance.now();

    // Process Token Activation
    processGestureToken(token, confidence, command);
    prevGestureToken = token;
  }

  // Process and animate matching gesture token
  function processGestureToken(token, confidence, command) {
    if (!VOCABULARY_TOKENS.includes(token)) {
      return;
    }

    const idFrag = tokenToId(token);
    const cardEl = document.getElementById(`card-${idFrag}`);
    const meterEl = document.getElementById(`meter-${idFrag}`);
    const countEl = document.getElementById(`count-${idFrag}`);
    const fbEl = document.getElementById(`fb-${idFrag}`);

    if (!cardEl) return;

    // Rising Edge Check: new gesture occurrence
    const isRisingEdge = (token !== prevGestureToken);

    if (isRisingEdge) {
      gestureMetrics[token].count++;
      if (countEl) {
        countEl.textContent = `Triggers: ${gestureMetrics[token].count}`;
      }
      // Execute widget-specific animation on rising edge to prevent multi-frame looping
      triggerWidgetAnimation(token, idFrag);
      sendInteractionFeedback(token, command, true);
    }

    // Update Confidence Meter Bar
    gestureMetrics[token].confidence = confidence;
    if (meterEl) {
      const pct = Math.round(confidence * 100.0);
      meterEl.style.width = `${pct}%`;
      if (pct >= 80) {
        meterEl.classList.add("high-conf");
      } else {
        meterEl.classList.remove("high-conf");
      }
    }

    // Activate Card Glow
    cardEl.classList.add("active-gesture");
    if (fbEl) {
      fbEl.textContent = `Status: ACTIVE (${Math.round(confidence * 100)}% Conf) -> ${command}`;
      fbEl.style.color = "#00E676";
    }

    // Clear active card glow after dwell timeout
    if (gestureMetrics[token].activeTimer) {
      clearTimeout(gestureMetrics[token].activeTimer);
    }
    gestureMetrics[token].activeTimer = setTimeout(() => {
      cardEl.classList.remove("active-gesture");
      if (fbEl && token !== "FIST" && token !== "PINCH_HOLD") {
        fbEl.textContent = `Status: Ready (Total: ${gestureMetrics[token].count})`;
        fbEl.style.color = "#64748B";
      }
      if (meterEl && token !== "OPEN_PALM") {
        meterEl.style.width = "0%";
      }
    }, 450);
  }

  // Trigger widget-specific dynamic feedback
  function triggerWidgetAnimation(token, idFrag) {
    switch (token) {
      case "PINCH_INDEX": {
        const btn = document.getElementById("widget-pinch-index");
        if (btn) {
          btn.classList.add("active-pulse");
          setTimeout(() => btn.classList.remove("active-pulse"), 250);
        }
        break;
      }
      case "PINCH_MIDDLE": {
        const popup = document.getElementById("popup-pinch-middle");
        if (popup) {
          popup.classList.remove("hidden");
          setTimeout(() => popup.classList.add("hidden"), 1000);
        }
        break;
      }
      case "PINCH_RING": {
        const box = document.getElementById("widget-pinch-ring");
        if (box) {
          box.classList.add("active-pulse");
          setTimeout(() => box.classList.remove("active-pulse"), 350);
        }
        break;
      }
      case "PINCH_PINKY": {
        const box = document.getElementById("widget-pinch-pinky");
        if (box) {
          box.classList.add("active-pulse");
          setTimeout(() => box.classList.remove("active-pulse"), 300);
        }
        break;
      }
      case "PINCH_HOLD": {
        const holdIndicator = document.getElementById("hold-state-indicator");
        const box = document.getElementById("widget-pinch-hold");
        if (holdIndicator) {
          holdIndicator.textContent = "State: Holding [DRAG ACTIVE]";
          holdIndicator.style.color = "#00E676";
        }
        if (box) box.classList.add("active-pulse");
        break;
      }
      case "PINCH_RELEASE": {
        const holdIndicator = document.getElementById("hold-state-indicator");
        const box = document.getElementById("widget-pinch-release");
        if (holdIndicator) {
          holdIndicator.textContent = "State: Released [DROP COMPLETE]";
          holdIndicator.style.color = "#FFB300";
        }
        if (box) {
          box.classList.add("active-pulse");
          setTimeout(() => box.classList.remove("active-pulse"), 400);
        }
        break;
      }
      case "SWIPE_LEFT": {
        const track = document.getElementById("carousel-track-left");
        const widgetBox = document.getElementById("widget-swipe-left");
        if (track) {
          leftCarouselIdx = (leftCarouselIdx + 1) % 3;
          track.style.transform = `translateX(-${leftCarouselIdx * 100}%)`;
          if (widgetBox) {
            widgetBox.classList.add("active-pulse");
            setTimeout(() => widgetBox.classList.remove("active-pulse"), 350);
          }
        }
        break;
      }
      case "SWIPE_RIGHT": {
        const track = document.getElementById("carousel-track-right");
        const widgetBox = document.getElementById("widget-swipe-right");
        if (track) {
          rightCarouselIdx = (rightCarouselIdx + 1) % 3;
          track.style.transform = `translateX(-${rightCarouselIdx * 100}%)`;
          if (widgetBox) {
            widgetBox.classList.add("active-pulse");
            setTimeout(() => widgetBox.classList.remove("active-pulse"), 350);
          }
        }
        break;
      }
      case "SWIPE_UP": {
        const scrollBox = document.getElementById("widget-swipe-up-scroll");
        if (scrollBox) {
          scrollBox.scrollTop = Math.max(0, scrollBox.scrollTop - 60);
          scrollBox.classList.add("active-pulse");
          setTimeout(() => scrollBox.classList.remove("active-pulse"), 350);
        }
        break;
      }
      case "SWIPE_DOWN": {
        const scrollBox = document.getElementById("widget-swipe-down-scroll");
        if (scrollBox) {
          scrollBox.scrollTop += 60;
          scrollBox.classList.add("active-pulse");
          setTimeout(() => scrollBox.classList.remove("active-pulse"), 350);
        }
        break;
      }
      case "OPEN_PALM": {
        const dwellBar = document.getElementById("dwell-open-palm");
        if (dwellBar) {
          dwellBar.style.width = "100%";
          setTimeout(() => { dwellBar.style.width = "0%"; }, 500);
        }
        break;
      }
      case "FIST": {
        const shieldBox = document.getElementById("widget-fist");
        const shieldLabel = document.getElementById("shield-status");
        if (shieldBox) shieldBox.classList.add("shield-locked");
        if (shieldLabel) {
          shieldLabel.textContent = "MIDAS TOUCH SUPPRESSED";
          shieldLabel.style.color = "#00E676";
        }
        setTimeout(() => {
          if (shieldBox) shieldBox.classList.remove("shield-locked");
          if (shieldLabel) {
            shieldLabel.textContent = "SHIELD ACTIVE: READY";
            shieldLabel.style.color = "#00E676";
          }
        }, 800);
        break;
      }
      case "THUMBS_UP": {
        const stamp = document.getElementById("confirm-status");
        if (stamp) {
          stamp.classList.remove("hidden");
          setTimeout(() => stamp.classList.add("hidden"), 1200);
        }
        break;
      }
    }
  }

  // Reset single card
  function resetGestureCard(token) {
    if (!gestureMetrics[token]) return;
    gestureMetrics[token].count = 0;
    const idFrag = tokenToId(token);
    const countEl = document.getElementById(`count-${idFrag}`);
    const meterEl = document.getElementById(`meter-${idFrag}`);
    const fbEl = document.getElementById(`fb-${idFrag}`);

    if (countEl) countEl.textContent = "Triggers: 0";
    if (meterEl) meterEl.style.width = "0%";
    if (fbEl) {
      fbEl.textContent = `Status: Waiting for ${token}...`;
      fbEl.style.color = "#64748B";
    }
  }

  // Reset All Cards
  if (btnResetAll) {
    btnResetAll.addEventListener("click", function () {
      VOCABULARY_TOKENS.forEach(token => resetGestureCard(token));
    });
  }

  // Individual reset buttons
  document.querySelectorAll(".btn-reset-card").forEach(btn => {
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      const targetToken = btn.getAttribute("data-target");
      if (targetToken) {
        resetGestureCard(targetToken);
      }
    });
  });

  // Interactive direct click fallback on widgets for manual testing
  document.querySelectorAll(".gesture-card").forEach(card => {
    card.addEventListener("click", function () {
      const token = card.getAttribute("data-token");
      if (token) {
        processGestureToken(token, 1.0, "MANUAL_CLICK_TEST");
      }
    });
  });

  // Send feedback packet to server
  function sendInteractionFeedback(gestureToken, actionType, success) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const payload = {
        type: "INTERACTION_EVENT",
        target_id: `GESTURE_${gestureToken}`,
        action_type: actionType,
        is_successful: success,
        timestamp: Date.now() / 1000.0
      };
      socket.send(JSON.stringify(payload));
    }
  }

  // Connect WebSocket to Python Server
  function connectWebSocket() {
    const wsUrl = "ws://127.0.0.1:8080/ws";
    socket = new WebSocket(wsUrl);

    socket.onopen = function () {
      elStatusConn.textContent = "CONNECTED (60 FPS)";
      elStatusConn.className = "telemetry-value status-online";
    };

    socket.onmessage = function (event) {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "PERCEPTION_UPDATE") {
          handlePerceptionUpdate(msg);
        }
      } catch (err) {
        console.error("Error parsing WebSocket packet:", err);
      }
    };

    socket.onclose = function () {
      elStatusConn.textContent = "OFFLINE (Retrying in 2s)";
      elStatusConn.className = "telemetry-value status-offline";
      setTimeout(connectWebSocket, 2000);
    };

    socket.onerror = function () {
      elStatusConn.textContent = "CONNECTION ERROR";
      elStatusConn.className = "telemetry-value status-offline";
    };
  }

  // Mouse fallback when disconnected
  window.addEventListener("mousemove", function (e) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      currentGazeX = e.clientX;
      currentGazeY = e.clientY;
      handlePerceptionUpdate({
        gaze_x: e.clientX,
        gaze_y: e.clientY,
        norm_gaze_x: e.clientX / window.innerWidth,
        norm_gaze_y: e.clientY / window.innerHeight,
        active_mode: "SIMULATED_MOUSE",
        gesture_token: "NONE",
        gesture_confidence: 0.0,
        command: "NO_ACTION"
      });
    }
  });

  // Start WebSocket client
  connectWebSocket();

})();
