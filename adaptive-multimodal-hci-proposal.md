# Project Proposal

## Project Title
# Self-Evaluating Adaptive Multimodal Decision Architecture for Human-Computer Interaction

---

## 1. Executive Summary & Scientific Contribution

Human-Computer Interaction (HCI) has progressively shifted from physical input peripherals (keyboards, mice) toward touchless, natural modalities including ocular gaze, head pose orientation, and spatial hand gestures. While combining multiple perceptual cues (multimodal fusion) provides theoretical resilience against single-sensor failures, conventional systems predominantly rely on **static, rule-based fusion engines** characterized by fixed boolean logic and population-averaged decision thresholds.

Such static designs suffer from a fundamental limitation: they assume a standardized user that does not exist in reality. Differences in ocular physiology, corrective lenses, hand kinematics, motor stability, and seating posture cause static thresholds to systematically fail—manifesting as either excessive false activations (loss of control) or frustrating false rejections (sluggish responsiveness).

### Core Research Thesis
This project introduces a **Runtime Self-Evaluating Adaptive Decision Architecture** that continuously observes, validates, and personalizes multimodal decision policies in real time through asynchronous implicit behavioral feedback. Operating without explicit user labeling, large external datasets, or deep learning computational overhead, the framework treats the multimodal vision pipeline as a non-intrusive domain vehicle. It introduces a closed-loop learning paradigm wherein real-time interaction feedback continuously personalizes per-user modality weights and activation thresholds under strict runtime validation gates.

---

## 2. Research Problem & Theoretical Motivation

### 2.1 The Inherent Failure of Static Thresholds
In multimodal interaction systems, decision boundaries are typically hardcoded or calibrated once across a cohort of lab participants. However, individual variability undermines this paradigm across three primary dimensions:
1. **Ocular Variability**: Corneal reflection, pupil size, eye aperture, corrective eyewear, and screen distance introduce continuous noise into gaze estimation.
2. **Kinematic Variability**: Gesture syntax (e.g., pinch aperture, swipe velocity, wrist acceleration) varies significantly across individuals based on anatomy, motor dexterity, and personal habits.
3. **Postural & Biomechanical Drift**: Seating posture, head-tilt baselines, and ambient lighting shift naturally over extended sessions, causing fixed spatial thresholds to degrade silently.

### 2.2 The Limitations of Conventional Solutions
Existing attempts to address user diversity typically adopt one of two extremes:
* *Cumbersome Explicit Calibration*: Requiring users to perform lengthy, multi-minute training tasks prior to interaction, which introduces severe onboarding friction.
* *Black-Box Offline Deep Learning*: Training complex neural models on massive datasets, which requires substantial computational resources (GPUs), lacks interpretability, cannot run locally on standard consumer CPUs, and cannot adapt dynamically to real-time session drift.

**Research Objective**: To design, implement, and validate a lightweight, interpretable, and self-evaluating decision architecture that personalizes decision parameters dynamically during standard use via implicit supervisory signals.

---

## 3. Formal Research Questions

The architectural design, runtime metrics, and empirical validation protocols are structured around four formal research questions:

* **RQ1 (Personalization Effectiveness)**: Does online parameter personalization driven by implicit feedback significantly reduce interaction errors (False Activation Rate, False Rejection Rate) and Task Completion Time compared to static multimodal fusion baselines?
* **RQ2 (Implicit Supervision Viability)**: Can continuous, decay-weighted implicit behavioral feedback provide sufficient supervision to steer parameter updates reliably without requiring explicit user labeling?
* **RQ3 (Runtime Self-Assessment Accuracy)**: Can a dedicated runtime assessment engine reliably determine when an interaction signal is trustworthy, and accurately quantify whether online updates improve or degrade interaction quality in real time?
* **RQ4 (Longitudinal Retention & Robustness)**: Can learned user profiles maintain stability and reduce cold-start friction across multiple sessions, while robustly adapting to environmental and behavioral drift via sequential hypothesis testing?

---

## 4. Principled Six-Layer Architecture

To maintain strict modularity and eliminate monolithic coupling, the system is organized into six orthogonal layers, each fulfilling a single architectural responsibility:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           THE SIX PRINCIPLED ARCHITECTURAL LAYERS                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [LAYER 1: PERCEPTION]      ──► Observes:     Extracts raw physical cues from webcam stream      │
│  [LAYER 2: CALIBRATION]     ──► Personalizes: Bootstraps user anatomy, noise variances & tempo   │
│  [LAYER 3: DECISION]        ──► Decides:      Fuses confidence, verifies safety & dispatches     │
│  [LAYER 4: OBSERVATION]     ──► Evaluates:    Monitors post-action user behavior via implicit cues│
│  [LAYER 5: ASSESSMENT]      ──► Validates:    Computes health metrics & gatekeeps updates        │
│  [LAYER 6: LEARNING]        ──► Learns:       Executes micro/macro SGD, simplex & profile store  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           CLOSED-LOOP ADAPTIVE FEEDBACK PIPELINE                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│           ┌─────────────────────────────────────────────────────────────┐                        │
│           │                   LAYER 1: PERCEPTION                       │                        │
│           │    (Webcam 30 FPS → FaceMesh/Iris + Hands + SolvePnP)       │                        │
│           └──────────────────────────────┬──────────────────────────────┘                        │
│                                          │ Feature Vector x                                      │
│                                          ▼                                                       │
│  ┌────────────────────────┐      ┌──────────────────────────────┐                                │
│  │ VERSIONED PROFILE STORE│─────►│      LAYER 3: DECISION       │                                │
│  │ (Profile v_k, ACI_t)   │      │ (3A Fusion → 3B Safety Reason│                                │
│  └───────────▲────────────┘      │  → 3C OS Context Dispatch)   │                                │
│              │                   └──────────────┬───────────────┘                                │
│              │ Profile v_k+1                    │ Executed Action Context                        │
│              │                                  ▼                                                │
│  ┌───────────┴────────────┐      ┌──────────────────────────────┐                                │
│  │    LAYER 6: LEARNING   │      │     LAYER 4: OBSERVATION     │                                │
│  │ (Micro SGD + Macro     │      │ (Temporal Windowing State    │                                │
│  │  Epoch State Machine)  │      │  Machine + 5 Sub-Detectors)  │                                │
│  └───────────▲────────────┘      └──────────────┬───────────────┘                                │
│              │ Validated Signal                 │ Observed Feedback Event                        │
│              │ (APPROVE)                        ▼                                                │
│              │                   ┌──────────────────────────────┐                                │
│              └───────────────────│     LAYER 5: ASSESSMENT      │                                │
│                                  │ (5A Metrics Engine +         │                                │
│                                  │  5B Decision Validator)      │                                │
│                                  └──────────────────────────────┘                                │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Core Technical Innovations

### 5.1 Interactive Calibration Wizard (Layer 2)
An onboarding protocol (60–90 seconds, 10–15 sample interactions) bootstraps the initial profile (`Profile v1`):
* **Neutral Posture 95% Confidence Ellipsoid**: Computes 3D head pose mean $\boldsymbol{\mu}_{\text{pose}}$ and inverted covariance $\boldsymbol{\Sigma}_{\text{pose}}^{-1}$ to establish a Mahalanobis neutral resting boundary.
* **5-Point Ocular Gaze Affine Mapping**: Fits a 2D affine perspective matrix $\mathbf{M}_{\text{gaze}}$ mapping pupil ratio coordinates to screen coordinates.
* **Kinematic & Tempo Profiling**: Measures user gesture velocity, wrist acceleration, and reaction latency to calibrate the user-specific decay constant $\tau_{\text{user}}$.
* **Variance-Informed Weight Initialization**: Assigns initial modality weights inversely proportional to observed sensor noise variances ($\tilde{w}_i^{(0)} \propto 1/\sigma_i^2$), compensating for individual sensor limitations (e.g. lower gaze weight for users wearing thick glasses).

### 5.2 Implicit Feedback Observer & Temporal State Machine (Layer 4)
Replaces intrusive feedback prompts with an asynchronous temporal observer operating across four distinct timing windows:
1. **Refractory Window ($[t_0, t_0 + 200\text{ms}]$)**: Filters out physiological motor inertia based on human visual-motor reaction time limits.
2. **Active Correction Window ($[t_0 + 200\text{ms}, t_0 + 1.8\text{s}]$)**: Intercepts corrective user actions via five specialized sub-detectors:
   * *Global OS Undo Hook*: Captures `Ctrl+Z`, `Alt+Left`, and `Ctrl+Shift+T` on matching target process IDs.
   * *Directional Oppositional Reversals*: Detects immediate inverse continuous commands (e.g., Scroll Down $\to$ Scroll Up within 1.0s).
   * *Rapid Duplicate Gesture Retries*: Detects repeated gesture attempts indicating a false rejection.
   * *Immediate Window/Tab Dismissal*: Detects rapid closure of newly opened windows within 1.5s.
   * *Physical Input Overrides*: Captures sudden mouse or keyboard intervention following an action.
3. **Stability Expiration Window ($t > t_0 + 1.8\text{s}$)**: Emits implicit positive acceptance ($c_{fb} = 1.0, y_{\text{target}} = 1.0$) when an action persists without reversal.
4. **Continuous Feedback Confidence Decay**:
   $$c_{fb}(\Delta t) = \begin{cases} \exp\left(-\frac{\Delta t - 0.20}{\tau_{\text{user}}}\right) & \text{for negative corrections with } \Delta t \in [0.2\text{s}, 1.8\text{s}] \\ 1.0 & \text{for positive acceptance after } 1.8\text{s} \\ 0.0 & \text{for neutral / ambiguous states} \end{cases}$$

### 5.3 Global Uncertainty & Confidence Propagation Pipeline
Unifies perceptual, decision, supervisory, and historical calibration metrics into an integrated confidence model:
$$C_{\text{update}} = \left(\frac{1}{1 + \sigma_{\text{perceptual}}}\right) \cdot g_{\text{weight}}(\Delta_{\text{decision}}) \cdot c_{fb}(\Delta t) \cdot (1 - \text{ECE}_t) \cdot ACI_t$$
where $C_{\text{update}}$ directly modulates the effective stochastic gradient descent step size ($\eta_{\text{eff}} = \eta_0 \cdot C_{\text{update}}$).

### 5.4 Dual-Scale Adaptation Engine (Layer 6)
* **Micro Adaptation (Per-Interaction SGD, $<1\text{ms}$)**: Immediately updates weights $\mathbf{w}_a$ and thresholds $\theta_a$ using ambiguity-gated gradients and exact 1D bisection box-constrained simplex projection ($w_{a, i} \in [0.05, 0.85], \sum w_{a, i} = 1.0$).
* **Macro Adaptation (Periodic Epochs, Every $N=30\text{--}50$ Interactions)**: Re-estimates running Gaussian score distributions ($\mu_S, \sigma_S$), recalculates Expected Calibration Error ($ECE$), evaluates Wald Sequential Probability Ratio Tests (SPRT) for drift detection, executes macro policies (`MERGE`, `FREEZE`, `DISCARD`, `RECALIBRATE`), and persists immutable `ProfileSnapshot` records.

### 5.5 Runtime Assessment Engine & Intelligent Gatekeeper (Layer 5)
* **Categorized Health Metrics**: Tracks EWMA Adaptation Gain ($AG_t$, $\alpha=0.10$), Sliding Learning Velocity ($LV_t$), Weight Stability Index ($WSI_t$), Adaptation Confidence Index ($ACI_t$), Expected Calibration Error ($ECE_t$), Recovery Rate ($RR$), and Drift Recovery Time ($DRT$).
* **Intelligent Gatekeeper**: Firewalls the learning engine by evaluating sample count floors ($k \ge 3$), confidence floors ($c_{fb} \ge 0.40$), macro drift lockouts ($S_m \ge 2.89$), contradiction resolution, and sensor signal-to-noise ratios, emitting strict `APPROVE` vs. `REJECT` verdicts.

---

## 6. Real-World Applications & Impact

| Application Domain | Primary User Variability | Core Adaptive Mechanism Applied |
|---|---|---|
| **Assistive Technology** | Atypical motor envelopes, tremor, muscle fatigue | Calibration wizard + continuous micro-adaptation + drift recalibration |
| **Sterile / Touchless Environments** | Personal gesture syntax, critical precision | Tier-2 safety confirmation gate + per-user versioned profiles |
| **Smart Workstations** | Posture drift, seating distance, lighting variations | Weight adaptation + macro drift detection + explainability HUD |
| **Public Kiosks / Shared Terminals** | Diverse uncalibrated users, short interaction spans | Fast 60s bootstrapping + rapid within-session implicit tuning |
| **Industrial / Safety HMIs** | Personal protective equipment (gloves, helmets, glasses) | Variance-informed weight initialization + fatigue-correlated drift alerts |

---

## 7. Empirical Evaluation & Scientific Validation Plan

To rigorously evaluate the framework against standard scientific benchmarks, a five-stage empirical validation protocol will be executed:

```
┌────────────────────────────────────────────────────────────────────────┐
│                 5-STAGE SCIENTIFIC VALIDATION PIPELINE                 │
├────────────────────────────────────────────────────────────────────────┤
│  Stage 1: Developer Verification & Invariant Testing                   │
│  • Simplex bounds (∑w_i=1, w_i∈[0.05, 0.85]), Wald SPRT renewal       │
│  • RAE module decoupling & Gatekeeper APPROVE/REJECT unit tests        │
├────────────────────────────────────────────────────────────────────────┤
│  Stage 2: Counterbalanced Pilot Evaluation (N = 4–6 Participants)      │
│  • Within-subjects A/B protocol across isomorphic task scripts         │
│  • 5-min washout period between Static Baseline and Adaptive Engine    │
├────────────────────────────────────────────────────────────────────────┤
│  Stage 3: Objective Telemetry & Adaptation Metrics Extraction          │
│  • Extract FAR, FRR, TCT, AG, RR, WSI, ECE, ACI from RAE telemetry    │
│  • Segment session into 5 epochs to verify learning curves             │
├────────────────────────────────────────────────────────────────────────┤
│  Stage 4: Subjective UX & Workload Profiling                           │
│  • Administer SUS, Raw NASA-TLX, and 7-item Adaptation Scale           │
├────────────────────────────────────────────────────────────────────────┤
│  Stage 5: Statistical Significance & Comparative Modeling              │
│  • Paired Wilcoxon Signed-Rank Tests (Static vs Adaptive)              │
│  • Optional: Linear Mixed-Effects Model isolating Condition×Order      │
└────────────────────────────────────────────────────────────────────────┘
```

### Standardized Evaluation Instruments
1. **Objective Telemetry**: False Activation Rate (FAR), False Rejection Rate (FRR), Task Completion Time (TCT), Adaptation Gain ($AG$), Expected Calibration Error ($ECE$), and Learning Velocity ($LV$).
2. **Standardized Usability**: System Usability Scale (SUS, 0–100 score).
3. **Cognitive Workload**: Raw NASA-TLX (Mental, Physical, Temporal, Performance, Effort, Frustration).
4. **Adaptation-Specific Likert Instrument**: 7-item scale evaluating perceived adaptability, predictability, recovery fluency, and visual transparency.

---

## 8. Technical Stack & Execution Constraints

* **Programming Language**: Python 3.11+
* **Computer Vision & Landmark Tracking**: OpenCV, MediaPipe (FaceMesh with Iris, Hands)
* **Numerical & Optimization Engine**: NumPy, SciPy (Custom 1D Bisection Simplex Projection)
* **OS Automation & Hooking**: PyAutoGUI, Windows Native Hook API (`SetWindowsHookEx` / `pynput`)
* **State-Aware Explainability Overlay**: PyQt6 / OpenGL HUD Overlay
* **Telemetry & Profile Store**: SQLite, JSON (Immutable `ProfileSnapshot` repository)
* **Hardware Target**: Standard consumer hardware (Standard 720p/1080p webcam, 8 GB RAM, CPU-only execution $<33\text{ms}/\text{frame}$, no GPU required).

---

## 9. Conclusion

By shifting the core research focus from raw feature extraction to a **self-evaluating adaptive decision architecture**, this framework directly resolves the primary limitation of multimodal interaction: the failure of static thresholds across diverse human populations. Through variance-informed calibration, continuous implicit feedback observation, global uncertainty modeling, and dual-scale micro/macro adaptation, the system delivers an intelligent, non-intrusive, and mathematically defensible HCI platform capable of personalizing itself seamlessly during natural desktop use.
