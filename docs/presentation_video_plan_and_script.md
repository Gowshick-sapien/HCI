# Multimodal HCI Demonstration Video Plan and Voiceover Script

**Project Title**: Self-Evaluating Adaptive Multimodal Decision & Assessment Architecture  
**Presenter**: Gowshick S (Reg No: 23BCE1200)  
**Target Duration**: 4 minutes to 4 minutes 30 seconds  
**Format**: On-Screen Screen Recording + Audio Voiceover  
**Prerequisites**: Webcam connected, browser open to Test Bench Suite (`http://127.0.0.1:8080`), terminal ready.  

---

## Video Structure Overview

| Scene | Section Title | Target Timestamp | Visual Cue / Screen Display | Core Objective |
| :--- | :--- | :--- | :--- | :--- |
| **Scene 1** | Introduction & Identification | 0:00 - 0:20 (20s) | Title slide or IDE showing Project Title & Name | Establish identity, credentials, and project title. |
| **Scene 2** | Problem Statement & Proposed Solution | 0:20 - 0:50 (30s) | Slide / Architecture Diagram (Six Layers) | Concise 30s elevator pitch addressing Midas Touch & OS safety. |
| **Scene 3** | User Profile Creation & Calibration | 0:50 - 1:30 (40s) | Running 9-Point Desktop Calibration GUI | Demonstrate personalized eye-gaze and head pose calibration. |
| **Scene 4** | Interactive Test Bench Demonstration (8 States) | 1:30 - 3:45 (135s) | Live Test Bench Suite (`localhost:8080`) | Step-by-step verification of all 8 target scenarios. |
| **Scene 5** | Quantitative Benchmarks & Conclusion | 3:45 - 4:15 (30s) | Benchmark tables (`docs/PROJECT_RESULTS...docx`) | Present 15.27 ms latency, 65.5 FPS, and 94/94 test pass rate. |

---

## Detailed Scene-by-Scene Script

### Scene 1: Introduction & Identification (0:00 - 0:20)

* **Visual on Screen**: 
  Display the title slide or clean header in the IDE / document:
  * Title: *Self-Evaluating Adaptive Multimodal Decision & Assessment Architecture for Human-Computer Interaction*
  * Presenter: *Gowshick S*
  * Registration Number: *23BCE1200*
* **Voiceover Script**:
  > "Hello everyone. My name is Gowshick S, registration number 23BCE1200. Today, I am presenting my project: the Self-Evaluating Adaptive Multimodal Decision and Assessment Architecture for Human-Computer Interaction."

---

### Scene 2: Problem Statement & Proposed Solution (0:20 - 0:50)

* **Visual on Screen**: 
  Display the six-layer architectural flow or a clean graphic illustrating Gaze, Head, and Hand inputs fusing into the Modality Arbiter.
* **Voiceover Script**:
  > "Traditional hands-free computing suffers from three major limitations: first, the Midas Touch problem, where natural eye gaze accidentally clicks everything you look at; second, ocular micro-jitter that causes target instability; and third, the safety hazard of raw computer vision directly hijacking the operating system mouse cursor.
  > 
  > To solve this, I designed a closed-loop multimodal architecture. It uses a single standard webcam to track eye gaze, head orientation, and hand kinematics simultaneously. Actions are only executed when an eye-gaze target anchor is confirmed by a discrete physical gesture, like an index pinch. Furthermore, all evaluations run safely inside a dedicated, sandboxed browser testbench, completely eliminating operating system hijacking."

---

### Scene 3: User Profile Creation & Calibration (0:50 - 1:30)

* **Visual on Screen**: 
  Open the terminal, execute the calibration wizard command:
  `python -m src.calibration.calibration_wizard default_user`
  Show the fullscreen 9-point calibration grid with animated pacing dots, followed by the verification pass.
* **Voiceover Script**:
  > "The first step in our workflow is User Profile Creation and Calibration.
  > 
  > Every user possesses unique eye geometry, interpupillary distance, and resting head angles. By launching our desktop calibration wizard, the system guides the user through a paced 9-point fixation grid, followed by a 5-point verification pass.
  > 
  > In the background, our solver computes a coupled affine transformation matrix and estimates the resting head pose covariance. Once completed, it stores these parameters directly into the user's isolated JSON profile under data/profiles, achieving an average gaze error of just 18 pixels on a full HD screen."

---

### Scene 4: Interactive Test Bench Demonstration - All 8 States (1:30 - 3:45)

* **Visual on Screen**: 
  In the terminal, run: `python scripts/run_testbench.py --user default_user`
  The browser opens `http://127.0.0.1:8080` showing the dark-themed Test Bench Suite with the top telemetry bar and the grid of 8 scenario cards. Point out the live eye-gaze reticle moving smoothly.

#### State 1: Primary Click & Discrete Counter (TC-TB-01) [1:30 - 1:45]
* **Visual on Screen**: Look at **Card 01: Primary Click Target**. Perform an index finger pinch. Show the badge incrementing from 0 to 1, then 2. Next, deliberately perform a middle-finger or ring-finger pinch to show the yellow rejection warning on the status bar.
* **Voiceover Script**:
  > "Now, we enter the live interactive testbench. Notice the green gaze reticle tracking my eye fixations at 60 frames per second.
  > 
  > In Scenario 1, we verify primary click selection. I focus my gaze on the primary click target and execute an index pinch. The badge counter immediately increments by one. Notice our strict cross-finger disambiguation: if I accidentally pinch with my middle or ring finger, the system ignores it and alerts that Scenario 1 strictly requires an index pinch. This completely eliminates accidental traversal noise."

#### State 2: Gaze Dwell Intentionality Trigger (TC-TB-02) [1:45 - 2:00]
* **Visual on Screen**: Fixate gaze on **Card 02: Dwell Intentionality Target**. Keep your hand resting. The circular progress ring fills smoothly over 500 ms and pulses green with the message `Intent Confirmed (500ms Dwell)`.
* **Voiceover Script**:
  > "In Scenario 2, we test hands-free dwell intentionality. Without using any hand gestures, I fixate my gaze on the circular target. A circular progress ring smoothly sweeps 360 degrees, confirming user intent after exactly 500 milliseconds. This enables entirely hands-free interaction for accessibility."

#### State 3: Context Menu Secondary Click (TC-TB-03) [2:00 - 2:15]
* **Visual on Screen**: Look at **Card 03: Context Menu Secondary Click Target**. Perform a middle finger pinch (`PINCH_MIDDLE`). A dark context menu pops up directly under the gaze reticle.
* **Voiceover Script**:
  > "Scenario 3 validates secondary click functionality. I anchor my gaze on Target 3 and perform a middle-finger pinch. The system maps this token to a secondary right-click, instantly spawning a context menu precisely at my gaze coordinates."

#### State 4: Text Input & Keyboard Handoff (TC-TB-04) [2:15 - 2:35]
* **Visual on Screen**: Look at the text input field in **Card 04: Text Input & Keyboard Handoff**. Perform an index pinch to focus the input. The yellow badge `KEYBOARD ACTIVE [TYPING MODE]` appears. Type a few characters on your physical keyboard (e.g., `Multimodal Test`). Point out the status bar showing multimodal clicks paused while typing. Defocus the input or perform a `THUMBS_UP` gesture to release handoff.
* **Voiceover Script**:
  > "In Scenario 4, we test Text Input and Keyboard Handoff. I look at the input field and perform an index pinch to focus it. The interface immediately activates typing mode, displaying the yellow keyboard active badge. While I type on my physical keyboard, all multimodal gaze clicks and gesture executions are temporarily paused to prevent interference. As soon as I finish typing and defocus or perform a thumbs-up gesture, multimodal tracking seamlessly resumes."

#### State 5: Hierarchical Dropdown Selection (TC-TB-05) [2:35 - 2:50]
* **Visual on Screen**: Look at **Card 05: Dropdown Option Selector**. Pinch to open the dropdown list. Look down at the option `High Sensitivity Profile` (which highlights under gaze focus) and pinch. The dropdown collapses and updates the button label.
* **Voiceover Script**:
  > "Scenario 5 evaluates hierarchical dropdown selection. I fixate on the dropdown header and pinch to expand the list. I then shift my gaze to select the High Sensitivity Profile, which highlights under visual fixation, and execute a confirmation pinch. The dropdown collapses with the updated selection."

#### State 6: Continuous Kinetic Scroll Viewport (TC-TB-06) [2:50 - 3:10]
* **Visual on Screen**: Direct gaze at **Card 06: Kinetic Scroll Viewport**. With an open hand facing the camera, perform a brisk downward flick (`SWIPE_DOWN`). The list scrolls down smoothly. Perform a brisk upward flick (`SWIPE_UP`). The list scrolls back up.
* **Voiceover Script**:
  > "Scenario 6 demonstrates kinetic viewport scrolling. While maintaining visual focus on Card 6, I perform a brisk downward hand flick. The wrist velocity exceeds our 1.2 units-per-second threshold, triggering a downward kinetic scroll. Flicking my hand upward smoothly scrolls the content back up. Dynamic velocity takes priority over static hover, making scrolling natural and responsive."

#### State 7: Tier-2 High-Consequence Action Confirmation (TC-TB-07) [3:10 - 3:30]
* **Visual on Screen**: Look at **Card 07: Tier-2 Consequence Confirmation**. Show the circular dwell ring starting to fill. Deliberately glance away at 200 ms: show the dwell ring aborting and resetting to zero. Then, re-fixate and maintain gaze for the full 600 ms: the circle completes and triggers `TIER-2 ACTION EXECUTED (Reset Confirmed)`.
* **Voiceover Script**:
  > "Scenario 7 demonstrates high-consequence safety protection for critical actions like system resets. When I look at the reset target, a 600-millisecond confirmation ring begins filling. If my gaze glances away early, the action aborts immediately, preventing catastrophic accidental triggers. Only when I maintain deliberate fixation through the full 360-degree sweep does the reset execute."

#### State 8: Physical Mouse Takeover Override (TC-TB-08) [3:30 - 3:45]
* **Visual on Screen**: Move your physical hardware mouse on your desk. Point out **Card 08: Physical Mouse Takeover Override** immediately activating with `PHYSICAL MOUSE TAKEOVER ACTIVE` and the status updating to `Hardware mouse moved -> Gaze yielded to mouse`.
* **Voiceover Script**:
  > "Finally, Scenario 8 demonstrates instantaneous physical mouse takeover. The moment I touch and nudge my physical hardware mouse, the arbiter immediately yields priority to the physical device. The interface updates to show mouse takeover active, guaranteeing that the user always maintains absolute, zero-latency manual override authority whenever desired."

---

### Scene 5: Quantitative Benchmarks & Conclusion (3:45 - 4:15)

* **Visual on Screen**: 
  Switch to [`docs/PROJECT_RESULTS_AND_EVALUATION_REPORT.docx`](file:///d:/HCI/docs/PROJECT_RESULTS_AND_EVALUATION_REPORT.docx), highlighting Table 1 (Subsystem Latency Profile) and Table 4 (ISO 9241-411 comparison).
* **Voiceover Script**:
  > "To conclude, our architecture has been thoroughly verified through formal benchmarks. 
  > 
  > The total end-to-end pipeline latency is just 15.27 milliseconds, enabling sustained execution at 65.5 frames per second on standard commodity webcams without any expensive infrared hardware. Across 94 automated tests covering unit logic, integration flows, and microsecond benchmarks, our system achieved a 100% pass rate. 
  > 
  > By combining spatial gaze anchoring, discrete gesture confirmation, and a sandboxed browser testbed, we have achieved robust, hands-free multimodal interaction that completely eliminates Midas Touch errors and operating system hijacking.
  > 
  > Thank you for your time and evaluation."

---

## Practical Recording Checklist

1. **Camera Position**: Center your webcam at eye level, roughly 50 to 70 cm away in good indoor lighting.
2. **Calibration Recenter**: If the eye reticle feels offset at any time during recording, press the key **`C`** on your keyboard or look at the top-right **`RECENTER (C)`** button to re-zero the eye offset instantly.
3. **Screen Resolution**: Set display scaling to 100% at 1920x1080 resolution so all 8 cards fit cleanly on screen without needing page scroll.
4. **Pacing**: Speak at a steady, conversational pace (approximately 130 to 140 words per minute). Pause for half a second before each scenario action so the viewer's eye follows your reticle.
