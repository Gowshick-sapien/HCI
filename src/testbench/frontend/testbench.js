/**
 * Multimodal HCI Interactive Testbench Suite (TBS-D1)
 * Client-Side Interaction Engine & Hit-Testing Controller
 * Strictly Zero Emojis Across Entire Scope
 */

(function () {
  "use strict";

  // Telemetry DOM elements
  const elStatusConn = document.getElementById("status-connection");
  const elStatusModality = document.getElementById("status-modality");
  const elStatusGaze = document.getElementById("status-gaze");
  const elStatusGesture = document.getElementById("status-gesture");
  const elStatusAction = document.getElementById("status-action");
  const elStatusLatency = document.getElementById("status-latency");
  const btnRecenter = document.getElementById("btn-recenter-gaze");

  // Interaction DOM Elements
  const canvasReticle = document.getElementById("gaze-reticle-canvas");
  const ctxReticle = canvasReticle.getContext("2d");

  // Scenario 1: Primary Click
  const cardPrimary = document.getElementById("card-primary-click");
  const btnPrimary = document.getElementById("btn-primary-click");
  const btnResetPrimary = document.getElementById("btn-reset-primary");
  const lblPrimaryCount = document.getElementById("primary-click-count");
  const fbPrimary = document.getElementById("feedback-primary-click");
  let primaryClickCount = 0;
  let lastPrimaryClickTime = 0.0;
  let lastScenario1FocusTime = 0.0;
  let lastPinchStartTime = 0.0;
  let wasPinchActive = false;

  // Scenario 2: Hover Dwell
  const cardHover = document.getElementById("card-hover-dwell");
  const zoneHover = document.getElementById("zone-hover-dwell");
  const barDwell = document.getElementById("dwell-progress-bar");
  const lblDwellTime = document.getElementById("dwell-time-label");
  const fbHover = document.getElementById("feedback-hover-dwell");
  let hoverDwellMs = 0.0;
  let lastHoverTimestamp = 0.0;
  let lastScenario2FocusTime = 0.0;

  // Scenario 3: Context Menu
  const cardContext = document.getElementById("card-context-menu");
  const btnSecondary = document.getElementById("btn-secondary-click");
  const menuContext = document.getElementById("context-menu-popup");
  const fbContext = document.getElementById("feedback-context-menu");
  let lastScenario3FocusTime = 0.0;

  // Scenario 4: Keyboard Handoff
  const cardKeyboard = document.getElementById("card-keyboard-handoff");
  const inputHandoff = document.getElementById("input-text-handoff");
  const badgeKeyboard = document.getElementById("keyboard-handoff-badge");
  const fbKeyboard = document.getElementById("feedback-keyboard-handoff");
  let isKeyboardHandoffActive = false;
  let lastScenario4FocusTime = 0.0;
  let handoffEngagedTimestamp = 0.0;

  // Scenario 5: Dropdown
  const cardDropdown = document.getElementById("card-dropdown-select");
  const dropdownHeader = document.getElementById("dropdown-header");
  const dropdownList = document.getElementById("dropdown-list");
  const dropdownSelectedText = document.getElementById("dropdown-selected-text");
  const fbDropdown = document.getElementById("feedback-dropdown-select");
  let isDropdownOpen = false;
  let lastScenario5FocusTime = 0.0;
  let dropdownOpenedTimestamp = 0.0;

  // Scenario 6: Kinetic Scroll
  const cardScroll = document.getElementById("card-scroll-viewport");
  const scrollContainer = document.getElementById("scroll-container");
  const fbScroll = document.getElementById("feedback-scroll-viewport");
  let lastScenario6FocusTime = 0.0;
  let lastScrollTimestamp = 0.0;

  // Scenario 7: Tier-2 Confirmation
  const cardTier2 = document.getElementById("card-tier2-reset");
  const btnTier2 = document.getElementById("btn-tier2-reset");
  const strokeDwell = document.getElementById("dwell-stroke");
  const fbTier2 = document.getElementById("feedback-tier2-reset");
  let tier2DwellMs = 0.0;
  const TIER2_MAX_DWELL = 600.0;
  let lastScenario7FocusTime = 0.0;

  // Scenario 8: Mouse Override
  const cardMouse = document.getElementById("card-mouse-takeover");
  const zoneMouse = document.getElementById("zone-mouse-takeover");
  const lblMouseStatus = document.getElementById("mouse-override-status");
  const fbMouse = document.getElementById("feedback-mouse-takeover");

  // Runtime Coordinates & Calibration Offset
  let currentGazeX = window.innerWidth / 2.0;
  let currentGazeY = window.innerHeight / 2.0;
  let targetGazeX = window.innerWidth / 2.0;
  let targetGazeY = window.innerHeight / 2.0;
  let rawGazeX = window.innerWidth / 2.0;
  let rawGazeY = window.innerHeight / 2.0;
  let gazeOffsetX = 0.0;
  let gazeOffsetY = 0.0;
  let lastPhysicalMouseMoveTime = 0.0;

  let activeModality = "GESTURE";
  let lastGestureToken = "NONE";
  let lastSocketTimestamp = 0;
  let socket = null;

  // Resize canvas to full viewport
  function resizeCanvas() {
    canvasReticle.width = window.innerWidth;
    canvasReticle.height = window.innerHeight;
  }
  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  // Calibration recenter function
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
    if ((e.key === "c" || e.key === "C") && document.activeElement !== inputHandoff) {
      recenterGaze();
    }
  });

  // Determines the single active card by finding the closest card to (x, y)
  function getActiveTestCard(x, y) {
    const cards = document.querySelectorAll(".test-card");
    let closestCard = null;
    let minDistance = Infinity;

    cards.forEach(card => {
      const rect = card.getBoundingClientRect();
      const dx = Math.max(rect.left - x, 0, x - rect.right);
      const dy = Math.max(rect.top - y, 0, y - rect.bottom);
      const dist = Math.hypot(dx, dy);

      if (dist < minDistance) {
        minDistance = dist;
        closestCard = card;
      }
    });

    return closestCard;
  }

  // Draw Gaze Reticle (Refined, Subtle, Crisp Pointer with Smooth Lerp)
  function renderGazeReticle() {
    ctxReticle.clearRect(0, 0, canvasReticle.width, canvasReticle.height);

    // Smooth reticle interpolation (lerp) toward target
    const dx = targetGazeX - currentGazeX;
    const dy = targetGazeY - currentGazeY;
    const dist = Math.hypot(dx, dy);

    if (dist > 180) {
      // Saccade snap: jump immediately with zero lag
      currentGazeX = targetGazeX;
      currentGazeY = targetGazeY;
    } else if (dist > 0.5) {
      // Exponential lerp: 60/120 FPS butter-smooth gaze stabilization
      currentGazeX += dx * 0.35;
      currentGazeY += dy * 0.35;
    }

    if (activeModality !== "MOUSE_PRIORITY") {
      ctxReticle.save();

      const activeCard = getActiveTestCard(currentGazeX, currentGazeY);
      const isOverTextInput = (activeCard && activeCard.id === "card-keyboard-handoff") || isKeyboardHandoffActive;

      if (isOverTextInput) {
        // High-contrast clean I-Beam text pointer
        ctxReticle.beginPath();
        // Top horizontal serif
        ctxReticle.moveTo(currentGazeX - 8, currentGazeY - 12);
        ctxReticle.lineTo(currentGazeX + 8, currentGazeY - 12);
        // Vertical stem
        ctxReticle.moveTo(currentGazeX, currentGazeY - 12);
        ctxReticle.lineTo(currentGazeX, currentGazeY + 12);
        // Bottom horizontal serif
        ctxReticle.moveTo(currentGazeX - 8, currentGazeY + 12);
        ctxReticle.lineTo(currentGazeX + 8, currentGazeY + 12);
        ctxReticle.strokeStyle = "rgba(56, 189, 248, 0.9)";
        ctxReticle.lineWidth = 1.5;
        ctxReticle.stroke();
      } else {
        // Subtle outer ring
        ctxReticle.beginPath();
        ctxReticle.arc(currentGazeX, currentGazeY, 16, 0, 2 * Math.PI);
        ctxReticle.strokeStyle = "rgba(56, 189, 248, 0.65)";
        ctxReticle.lineWidth = 1.5;
        ctxReticle.stroke();

        // Inner center dot
        ctxReticle.beginPath();
        ctxReticle.arc(currentGazeX, currentGazeY, 2.5, 0, 2 * Math.PI);
        ctxReticle.fillStyle = "rgba(56, 189, 248, 0.9)";
        ctxReticle.fill();

        // Precise hairline crosshair ticks
        ctxReticle.beginPath();
        ctxReticle.moveTo(currentGazeX - 22, currentGazeY);
        ctxReticle.lineTo(currentGazeX - 16, currentGazeY);
        ctxReticle.moveTo(currentGazeX + 16, currentGazeY);
        ctxReticle.lineTo(currentGazeX + 22, currentGazeY);
        ctxReticle.moveTo(currentGazeX, currentGazeY - 22);
        ctxReticle.lineTo(currentGazeX, currentGazeY - 16);
        ctxReticle.moveTo(currentGazeX, currentGazeY + 16);
        ctxReticle.lineTo(currentGazeX, currentGazeY + 22);
        ctxReticle.strokeStyle = "rgba(56, 189, 248, 0.5)";
        ctxReticle.lineWidth = 1;
        ctxReticle.stroke();
      }

      ctxReticle.restore();
    }

    requestAnimationFrame(renderGazeReticle);
  }
  requestAnimationFrame(renderGazeReticle);

  // Check element intersection with optional padding margin
  function isPointInside(el, x, y, padding) {
    if (!el) return false;
    const pad = padding !== undefined ? padding : 0;
    const rect = el.getBoundingClientRect();
    return (
      x >= (rect.left - pad) &&
      x <= (rect.right + pad) &&
      y >= (rect.top - pad) &&
      y <= (rect.bottom + pad)
    );
  }

  // Handle incoming perception frame from WebSocket
  function handlePerceptionUpdate(data) {
    const now = performance.now();
    // Update coordinates from perception stream only if physical mouse hasn't moved recently
    if (now - lastPhysicalMouseMoveTime > 1200.0) {
      if (data.norm_gaze_x !== undefined && data.norm_gaze_y !== undefined) {
        rawGazeX = data.norm_gaze_x * window.innerWidth;
        rawGazeY = data.norm_gaze_y * window.innerHeight;
      } else if (data.gaze_x !== undefined && data.gaze_y !== undefined) {
        rawGazeX = (data.gaze_x / 1920.0) * window.innerWidth;
        rawGazeY = (data.gaze_y / 1080.0) * window.innerHeight;
      }

      targetGazeX = Math.max(0, Math.min(window.innerWidth, rawGazeX + gazeOffsetX));
      targetGazeY = Math.max(0, Math.min(window.innerHeight, rawGazeY + gazeOffsetY));
    }

    activeModality = data.active_mode || "GESTURE";
    lastGestureToken = data.gesture_token || "NONE";

    // Update Telemetry Bar
    elStatusModality.textContent = activeModality;
    elStatusGaze.textContent = `(${Math.round(currentGazeX)}, ${Math.round(currentGazeY)})`;
    elStatusGesture.textContent = `${lastGestureToken} (${(data.gesture_confidence || 0).toFixed(2)})`;
    elStatusAction.textContent = data.command || "NO_ACTION";

    const latency = (performance.now() - lastSocketTimestamp).toFixed(1);
    elStatusLatency.textContent = `${latency} ms`;
    lastSocketTimestamp = performance.now();

    // Process UI Hit Testing
    processHitTesting(data);
  }

  // Hit-testing logic across the 8 scenarios
  function processHitTesting(frameData) {
    const gx = currentGazeX;
    const gy = currentGazeY;
    const cmd = frameData.command || "NO_ACTION";
    const token = frameData.gesture_token || "NONE";
    const now = performance.now();

    // Determine the single active target card based on closest distance
    const activeCard = getActiveTestCard(gx, gy);
    const activeId = activeCard ? activeCard.id : null;

    // Update active visual highlights across cards
    document.querySelectorAll(".test-card").forEach(c => {
      if (c === activeCard) {
        c.classList.add("active-gaze");
      } else {
        c.classList.remove("active-gaze");
      }
    });

    // Strict identification of index pinch vs other finger pinches
    const isIndexPinch = (token === "PINCH_INDEX" || (cmd === "PRIMARY_CLICK" && token !== "PINCH_MIDDLE" && token !== "PINCH_RING" && token !== "PINCH_PINKY"));
    const isNonIndexPinch = (token === "PINCH_MIDDLE" || token === "PINCH_RING" || token === "PINCH_PINKY");
    const isPinchRisingEdge = isIndexPinch && !wasPinchActive;

    // --------------------------------------------------------------------------
    // Scenario 1: Primary Click Button (Strict PINCH_INDEX Enforcement)
    // --------------------------------------------------------------------------
    if (activeId === "card-primary-click") {
      btnPrimary.classList.add("gaze-hover");

      if (isNonIndexPinch) {
        fbPrimary.textContent = "Status: Ignored " + token + ". Scenario 01 strictly requires PINCH_INDEX.";
        fbPrimary.style.color = "#FFB300";
      } else if (isPinchRisingEdge && !isKeyboardHandoffActive) {
        lastPinchStartTime = now;
        triggerPrimaryClick();
      } else if (!isIndexPinch) {
        if (fbPrimary.textContent.indexOf("PRIMARY_CLICK") === -1 && fbPrimary.textContent.indexOf("Ignored") === -1) {
          fbPrimary.textContent = "Status: Target focused. Perform PINCH_INDEX to click.";
          fbPrimary.style.color = "#00E5FF";
        }
      }
    } else {
      btnPrimary.classList.remove("gaze-hover");
      if (fbPrimary.textContent.indexOf("PRIMARY_CLICK") === -1) {
        fbPrimary.textContent = "Status: Waiting for interaction...";
        fbPrimary.style.color = "#64748B";
      }
    }

    // --------------------------------------------------------------------------
    // Scenario 2: Gaze Hover Dwell Zone
    // --------------------------------------------------------------------------
    if (activeId === "card-hover-dwell") {
      zoneHover.classList.add("gaze-hover");
      const dt = lastHoverTimestamp > 0 ? (now - lastHoverTimestamp) : 16.0;
      lastHoverTimestamp = now;

      hoverDwellMs = Math.min(600.0, hoverDwellMs + dt);
      const pct = (hoverDwellMs / 600.0) * 100.0;
      barDwell.style.width = `${pct}%`;
      lblDwellTime.textContent = `Dwell: ${Math.round(hoverDwellMs)} ms`;

      if (hoverDwellMs >= 300.0) {
        zoneHover.classList.add("dwell-complete");
        fbHover.textContent = "Status: HOVER ACTIVE (Fixation Confirmed)";
        fbHover.style.color = "#00E676";
      } else {
        fbHover.textContent = `Status: DWELL PROGRESS: ${Math.round(hoverDwellMs)} / 300 ms`;
        fbHover.style.color = "#00E5FF";
      }
    } else {
      zoneHover.classList.remove("gaze-hover", "dwell-complete");
      hoverDwellMs = 0.0;
      lastHoverTimestamp = 0.0;
      barDwell.style.width = "0%";
      lblDwellTime.textContent = "Dwell: 0 ms";
      fbHover.textContent = "Status: No fixation detected";
      fbHover.style.color = "#64748B";
    }

    // --------------------------------------------------------------------------
    // Scenario 3: Secondary Click / Context Menu
    // --------------------------------------------------------------------------
    if (activeId === "card-context-menu") {
      btnSecondary.classList.add("gaze-hover");

      if (token === "PINCH_INDEX") {
        fbContext.textContent = "Status: Ignored PINCH_INDEX. Scenario 03 requires PINCH_MIDDLE.";
        fbContext.style.color = "#FFB300";
      } else if (cmd === "SECONDARY_CLICK" || cmd === "RIGHT_CLICK" || token === "PINCH_MIDDLE") {
        menuContext.classList.remove("hidden");
        fbContext.textContent = "Status: Context menu displayed via PINCH_MIDDLE / RIGHT_CLICK";
        fbContext.style.color = "#00E5FF";
        sendInteractionFeedback("TB-T03", "SECONDARY_CLICK", true);
      }
    } else {
      btnSecondary.classList.remove("gaze-hover");
    }

    // --------------------------------------------------------------------------
    // Scenario 4: Text Input & Keyboard Handoff
    // --------------------------------------------------------------------------
    if (isKeyboardHandoffActive && (token === "THUMBS_UP" || cmd === "CONFIRM_SUBMIT")) {
      if (now - handoffEngagedTimestamp > 1200.0) {
        deactivateKeyboardHandoff();
      }
    }

    if (activeId === "card-keyboard-handoff") {
      inputHandoff.classList.add("gaze-hover");
      if (!isKeyboardHandoffActive) {
        fbKeyboard.textContent = "Status: Focused on Scenario 4. Perform PRIMARY CLICK to activate text box.";
        fbKeyboard.style.color = "#00E5FF";
      }

      if (isPinchRisingEdge && !isKeyboardHandoffActive) {
        lastPrimaryClickTime = now;
        activateKeyboardHandoff();
      }
    } else {
      inputHandoff.classList.remove("gaze-hover");
    }

    // --------------------------------------------------------------------------
    // Scenario 5: Dropdown Selection
    // --------------------------------------------------------------------------
    if (activeId === "card-dropdown-select") {
      if (isDropdownOpen) {
        // Find option whose vertical center is closest to current gaze Y
        let matchedOption = null;
        let minOptDist = Infinity;
        const options = document.querySelectorAll(".dropdown-option");
        options.forEach(opt => {
          const rect = opt.getBoundingClientRect();
          const optCenterY = (rect.top + rect.bottom) / 2.0;
          const dist = Math.abs(gy - optCenterY);
          if (dist < minOptDist) {
            minOptDist = dist;
            matchedOption = opt;
          }
        });

        options.forEach(opt => {
          if (opt === matchedOption) {
            opt.classList.add("gaze-hover");
          } else {
            opt.classList.remove("gaze-hover");
          }
        });

        const isCooldownOver = (now - dropdownOpenedTimestamp > 250.0);

        if (matchedOption) {
          dropdownHeader.classList.remove("gaze-hover");
          fbDropdown.textContent = `Status: Focused on [${matchedOption.textContent}]. Perform PRIMARY CLICK to select.`;
          fbDropdown.style.color = "#00E5FF";

          if (isPinchRisingEdge && isCooldownOver) {
            lastPrimaryClickTime = now;
            dropdownSelectedText.textContent = matchedOption.textContent;
            dropdownList.classList.add("hidden");
            isDropdownOpen = false;
            options.forEach(o => o.classList.remove("gaze-hover"));
            fbDropdown.textContent = `Status: Selected [${matchedOption.textContent}] via PRIMARY CLICK`;
            fbDropdown.style.color = "#00E676";
            sendInteractionFeedback("TB-T05", "DROPDOWN_SELECT", true);
          }
        }
      } else {
        // Dropdown is closed
        dropdownHeader.classList.add("gaze-hover");
        if (fbDropdown.textContent.indexOf("Selected") === -1) {
          fbDropdown.textContent = "Status: Focused on Scenario 5. Perform PRIMARY CLICK to list dropdown options.";
          fbDropdown.style.color = "#00E5FF";
        }
        if (isPinchRisingEdge) {
          lastPrimaryClickTime = now;
          dropdownOpenedTimestamp = now;
          isDropdownOpen = true;
          dropdownList.classList.remove("hidden");
          fbDropdown.textContent = "Status: Dropdown listed. Gaze at any option and PRIMARY CLICK to select.";
          fbDropdown.style.color = "#00E5FF";
          sendInteractionFeedback("TB-T05", "DROPDOWN_OPEN", true);
        }
      }
    } else {
      dropdownHeader.classList.remove("gaze-hover");
    }

    // --------------------------------------------------------------------------
    // Scenario 6: Kinetic Scroll Viewport (Up, Down, Left, Right)
    // --------------------------------------------------------------------------
    const isSwipeUp = (token === "SWIPE_UP" || cmd === "SCROLL_UP");
    const isSwipeDown = (token === "SWIPE_DOWN" || cmd === "SCROLL_DOWN");
    const isSwipeLeft = (token === "SWIPE_LEFT" || cmd === "NAVIGATE_PREVIOUS");
    const isSwipeRight = (token === "SWIPE_RIGHT" || cmd === "NAVIGATE_NEXT");

    if (activeId === "card-scroll-viewport") {
      if (isSwipeUp || isSwipeDown || isSwipeLeft || isSwipeRight) {
        if (now - lastScrollTimestamp > 200.0) {
          lastScrollTimestamp = now;
          let scrollDelta = 0;
          let directionLabel = "";

          if (isSwipeUp) {
            scrollDelta = -120;
            directionLabel = "UP (SWIPE_UP)";
            scrollContainer.classList.add("scroll-pulse-up");
          } else if (isSwipeDown) {
            scrollDelta = 120;
            directionLabel = "DOWN (SWIPE_DOWN)";
            scrollContainer.classList.add("scroll-pulse-down");
          } else if (isSwipeLeft) {
            scrollDelta = -100;
            directionLabel = "LEFT (SWIPE_LEFT / PREV)";
            scrollContainer.classList.add("scroll-pulse-up");
          } else if (isSwipeRight) {
            scrollDelta = 100;
            directionLabel = "RIGHT (SWIPE_RIGHT / NEXT)";
            scrollContainer.classList.add("scroll-pulse-down");
          }

          scrollContainer.scrollBy({ top: scrollDelta, behavior: "smooth" });

          setTimeout(() => {
            scrollContainer.classList.remove("scroll-pulse-up", "scroll-pulse-down");
          }, 350);

          const maxScroll = Math.max(1, scrollContainer.scrollHeight - scrollContainer.clientHeight);
          const currentPos = Math.max(0, Math.min(maxScroll, scrollContainer.scrollTop + scrollDelta));
          const pct = Math.max(0, Math.min(100, Math.round((currentPos / maxScroll) * 100)));
          fbScroll.textContent = `Status: Scrolled ${directionLabel} (${Math.round(currentPos)}px / ${pct}%)`;
          fbScroll.style.color = "#00E676";
          sendInteractionFeedback("TB-T06", token, true);
        }
      }
    }

    // --------------------------------------------------------------------------
    // Scenario 7: Tier-2 High-Consequence Reset
    // --------------------------------------------------------------------------
    if (activeId === "card-tier2-reset") {
      btnTier2.classList.add("gaze-hover");

      tier2DwellMs = Math.min(TIER2_MAX_DWELL, tier2DwellMs + 16.0);
      const frac = tier2DwellMs / TIER2_MAX_DWELL;
      const offset = 113.0 * (1.0 - frac);
      strokeDwell.style.strokeDashoffset = offset;

      if (tier2DwellMs >= TIER2_MAX_DWELL) {
        btnTier2.classList.add("clicked");
        fbTier2.textContent = "Status: TIER-2 ACTION EXECUTED (Reset Confirmed)";
        fbTier2.style.color = "#FF3D00";
        sendInteractionFeedback("TB-T07", "TIER2_RESET_CONFIRMED", true);
        setTimeout(() => {
          btnTier2.classList.remove("clicked");
          tier2DwellMs = 0;
          strokeDwell.style.strokeDashoffset = 113.0;
        }, 1200);
      }
    } else {
      btnTier2.classList.remove("gaze-hover");
      tier2DwellMs = 0.0;
      strokeDwell.style.strokeDashoffset = 113.0;
    }

    // Record pinch state for edge detection in next frame
    wasPinchActive = isIndexPinch;
  }

  // Trigger Primary Click
  function triggerPrimaryClick() {
    const now = performance.now();
    lastPrimaryClickTime = now;

    primaryClickCount++;
    lblPrimaryCount.textContent = `Clicks: ${primaryClickCount}`;
    btnPrimary.classList.add("clicked");

    fbPrimary.textContent = `Status: PRIMARY_CLICK #${primaryClickCount} Triggered!`;
    fbPrimary.style.color = "#00E676";

    sendInteractionFeedback("TB-T01", "PRIMARY_CLICK", true);

    setTimeout(() => {
      btnPrimary.classList.remove("clicked");
    }, 200);
  }

  // Scenario 1 Reset Button
  if (btnResetPrimary) {
    btnResetPrimary.addEventListener("click", function () {
      primaryClickCount = 0;
      lblPrimaryCount.textContent = "Clicks: 0";
      fbPrimary.textContent = "Status: Counter reset to 0. Ready for interaction.";
      fbPrimary.style.color = "#64748B";
    });
  }

  // Native click listeners for manual or fallback operation
  btnPrimary.addEventListener("click", function () {
    triggerPrimaryClick();
  });

  zoneHover.addEventListener("click", function () {
    hoverDwellMs = 600.0;
    zoneHover.classList.add("dwell-complete");
    barDwell.style.width = "100%";
    lblDwellTime.textContent = "Dwell: 600 ms";
    fbHover.textContent = "Status: HOVER ACTIVE (Direct Click)";
    fbHover.style.color = "#00E676";
  });

  btnSecondary.addEventListener("click", function () {
    menuContext.classList.remove("hidden");
    fbContext.textContent = "Status: Context menu displayed via direct click";
    fbContext.style.color = "#00E5FF";
  });

  dropdownHeader.addEventListener("click", function () {
    isDropdownOpen = !isDropdownOpen;
    dropdownList.classList.toggle("hidden", !isDropdownOpen);
    fbDropdown.textContent = isDropdownOpen
      ? "Status: Dropdown opened via direct click."
      : "Status: Dropdown closed.";
  });

  document.querySelectorAll(".dropdown-option").forEach(opt => {
    opt.addEventListener("click", function (e) {
      e.stopPropagation();
      dropdownSelectedText.textContent = opt.textContent;
      dropdownList.classList.add("hidden");
      isDropdownOpen = false;
      document.querySelectorAll(".dropdown-option").forEach(o => o.classList.remove("gaze-hover"));
      fbDropdown.textContent = `Status: Selected [${opt.textContent}]`;
      fbDropdown.style.color = "#00E676";
      sendInteractionFeedback("TB-T05", "DROPDOWN_SELECT", true);
    });
  });

  btnTier2.addEventListener("click", function () {
    tier2DwellMs = TIER2_MAX_DWELL;
    btnTier2.classList.add("clicked");
    fbTier2.textContent = "Status: TIER-2 ACTION EXECUTED (Reset Confirmed)";
    fbTier2.style.color = "#FF3D00";
    sendInteractionFeedback("TB-T07", "TIER2_RESET_CONFIRMED", true);
    setTimeout(() => {
      btnTier2.classList.remove("clicked");
      tier2DwellMs = 0;
      strokeDwell.style.strokeDashoffset = 113.0;
    }, 1200);
  });

  // Trigger Keyboard Handoff
  function activateKeyboardHandoff() {
    isKeyboardHandoffActive = true;
    inputHandoff.focus();
    inputHandoff.classList.add("text-pointer-active");
    badgeKeyboard.classList.remove("hidden");
    fbKeyboard.textContent = "Status: TEXT POINTER ACTIVE [TYPING MODE]. Gesture clicks paused.";
    fbKeyboard.style.color = "#FFB300";
    sendInteractionFeedback("TB-T04", "KEYBOARD_HANDOFF_ENGAGED", true);
  }

  function deactivateKeyboardHandoff() {
    isKeyboardHandoffActive = false;
    inputHandoff.blur();
    inputHandoff.classList.remove("text-pointer-active");
    badgeKeyboard.classList.add("hidden");
    fbKeyboard.textContent = "Status: Multimodal active (Defocus or THUMBS_UP to exit)";
    fbKeyboard.style.color = "#64748B";
    sendInteractionFeedback("TB-T04", "KEYBOARD_HANDOFF_RELEASED", true);
  }

  inputHandoff.addEventListener("click", function () {
    activateKeyboardHandoff();
  });

  inputHandoff.addEventListener("keydown", function (e) {
    if (e.key === "Escape" || e.key === "Enter") {
      deactivateKeyboardHandoff();
    }
  });

  const btnScrollUp = document.getElementById("btn-scroll-up");
  const btnScrollDown = document.getElementById("btn-scroll-down");

  if (btnScrollUp) {
    btnScrollUp.addEventListener("click", function () {
      scrollContainer.scrollBy({ top: -80, behavior: "smooth" });
      scrollContainer.classList.add("scroll-pulse-up");
      setTimeout(() => scrollContainer.classList.remove("scroll-pulse-up"), 350);
      fbScroll.textContent = `Status: Scrolled UP manually (${scrollContainer.scrollTop}px)`;
      fbScroll.style.color = "#00E676";
      sendInteractionFeedback("TB-T06", "MANUAL_SCROLL_UP", true);
    });
  }

  if (btnScrollDown) {
    btnScrollDown.addEventListener("click", function () {
      scrollContainer.scrollBy({ top: 80, behavior: "smooth" });
      scrollContainer.classList.add("scroll-pulse-down");
      setTimeout(() => scrollContainer.classList.remove("scroll-pulse-down"), 350);
      fbScroll.textContent = `Status: Scrolled DOWN manually (${scrollContainer.scrollTop}px)`;
      fbScroll.style.color = "#00E676";
      sendInteractionFeedback("TB-T06", "MANUAL_SCROLL_DOWN", true);
    });
  }

  // Physical mouse movement detection (Scenario 8)
  window.addEventListener("mousemove", function (e) {
    lastPhysicalMouseMoveTime = performance.now();
    targetGazeX = e.clientX;
    targetGazeY = e.clientY;
    currentGazeX = e.clientX;
    currentGazeY = e.clientY;

    if (socket && socket.readyState === WebSocket.OPEN) {
      processHitTesting({
        command: "NO_ACTION",
        gesture_token: lastGestureToken,
        active_mode: activeModality
      });
    }

    if (e.movementX !== 0 || e.movementY !== 0) {
      zoneMouse.classList.add("mouse-active");
      lblMouseStatus.textContent = "PHYSICAL MOUSE TAKEOVER ACTIVE";
      lblMouseStatus.style.color = "#FFB300";
      fbMouse.textContent = "Status: Hardware mouse moved -> Gaze yielded to mouse";
      fbMouse.style.color = "#FFB300";

      sendInteractionFeedback("TB-T08", "IMPLICIT_MOUSE_TAKEOVER", true);

      setTimeout(() => {
        zoneMouse.classList.remove("mouse-active");
        lblMouseStatus.textContent = "Multimodal Mode Active";
        lblMouseStatus.style.color = "#94A3B8";
        fbMouse.textContent = "Status: Multimodal tracking active";
        fbMouse.style.color = "#64748B";
      }, 1000);
    }
  });

  // Send interaction telemetry to Python WebSocket server
  function sendInteractionFeedback(targetId, actionType, success) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const payload = {
        type: "INTERACTION_EVENT",
        target_id: targetId,
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

  // Mouse emulation fallback when disconnected
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
        gesture_confidence: 1.0,
        command: "NO_ACTION"
      });
    }
  });

  // Manual click emulation fallback when disconnected
  window.addEventListener("click", function (e) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      handlePerceptionUpdate({
        gaze_x: e.clientX,
        gaze_y: e.clientY,
        norm_gaze_x: e.clientX / window.innerWidth,
        norm_gaze_y: e.clientY / window.innerHeight,
        active_mode: "SIMULATED_MOUSE",
        gesture_token: "PINCH_INDEX",
        gesture_confidence: 1.0,
        command: "PRIMARY_CLICK"
      });
    }
  });

  // Start WebSocket client
  connectWebSocket();

})();
