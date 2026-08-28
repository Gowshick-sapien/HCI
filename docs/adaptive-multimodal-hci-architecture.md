# System Architecture Specification

## Project Title
# Self-Evaluating Adaptive Multimodal Decision & Assessment Architecture

---

## 1. Architectural Principles & Six-Layer Decomposition

To guarantee modularity, mathematical rigor, and complete separation of concerns, the system is structured into **six orthogonal layers**. Each layer fulfills exactly one core responsibility within the closed-loop decision lifecycle:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         THE REVISED PRINCIPLED ARCHITECTURAL LAYERS                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [LAYER 1 : PERCEPTION]     ──► Observes:     Extracts raw features & gaze dwell from webcam     │
│  [LAYER 1B: GESTURE VOCAB]  ──► Classifies:   Translates kinematics into named gesture tokens    │
│  [ARBITER : MODALITY GATE]  ──► Arbitrates:   Suppresses gesture eval during active device use   │
│  [LAYER 2 : CALIBRATION]    ──► Personalizes: Bootstraps anatomy, noise, gesture & dwell bases   │
│  [LAYER 3 : DECISION]       ──► Composes:     Resolves spatial target + intent, dispatches       │
│  [LAYER 4 : OBSERVATION]    ──► Evaluates:    Monitors post-action user behavior via implicit cues│
│  [LAYER 5 : ASSESSMENT]     ──► Validates:    Computes health metrics & gatekeeps updates        │
│  [LAYER 6 : LEARNING]       ──► Learns:       Executes micro/macro SGD, simplex & profile store  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Closed-Loop System Architecture

Unlike traditional feed-forward pipelines, the framework executes as an **active, continuous self-evaluating closed loop**:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      REVISED CLOSED-LOOP ADAPTIVE FEEDBACK PIPELINE                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│           ┌─────────────────────────────────────────────────────────────┐                        │
│           │                   LAYER 1: PERCEPTION                       │                        │
│           │  (Webcam 30 FPS → FaceMesh/Iris + Hands + SolvePnP +        │                        │
│           │   Gaze Dwell Tracker → gaze_dwell_ms, gaze_stability)       │                        │
│           └──────────────────────────────┬──────────────────────────────┘                        │
│                                          │ Raw Feature Vector + Dwell Metrics                    │
│                                          ▼                                                       │
│           ┌─────────────────────────────────────────────────────────────┐                        │
│           │             LAYER 1B: GESTURE VOCABULARY ENGINE             │                        │
│           │  (Kinematics → Named Token: PINCH / FIST / SWIPE / ...      │                        │
│           │   Output: gesture_token, c_gesture, requires_gaze_target)   │                        │
│           └──────────────────────────────┬──────────────────────────────┘                        │
│                                          │ GestureClassification                                 │
│                                          ▼                                                       │
│           ┌─────────────────────────────────────────────────────────────┐                        │
│           │                  ACTIVE MODALITY ARBITER                    │                        │
│           │  (FIST → NO_ACTION / keyboard_active → SUPPRESS /           │                        │
│           │   mouse_active → SOFT_REDUCE / clear → GESTURE mode)        │                        │
│           └──────────────────────────────┬──────────────────────────────┘                        │
│                                          │ Gated Feature + Gesture Token                         │
│                                          ▼                                                       │
│  ┌────────────────────────┐      ┌──────────────────────────────┐                                │
│  │ VERSIONED PROFILE STORE│─────►│      LAYER 3: DECISION       │                                │
│  │ (Profile v_k, ACI_t)   │      │ (3A Command Composer →       │                                │
│  └───────────▲────────────┘      │  3B Safety + Tier 0 Gate →   │                                │
│              │                   │  3C OS Dispatch + KB Handoff) │                                │
│              │ Profile v_k+1     └──────────────┬───────────────┘                                │
│              │                                  │ Executed Action Context                        │
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

## 3. End-to-End Decision Lifecycle Sequence

The following sequence diagram defines the execution path of a single interaction cycle from raw visual capture to persistent profile adaptation:

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant L1 as Layer 1: Perception
    participant L1B as Layer 1B: Gesture Vocab
    participant ARB as Modality Arbiter
    participant L3A as Layer 3A: Command Composer
    participant L3B as Layer 3B: Safety Reasoning
    participant OS as OS / Desktop Dispatcher
    participant L4 as Layer 4: Feedback Observer
    participant L5 as Layer 5: Runtime Assessment (RAE)
    participant L6 as Layer 6: Adaptive Learner
    participant DB as Profile Store (v_k)

    User->>L1: Performs physical gesture & gaze glance
    L1->>L1B: Emits raw kinematics + gaze_dwell_ms + gaze_stability
    L1B->>L1B: Classifies gesture_token (PINCH / FIST / SWIPE / ...)
    L1B->>ARB: Emits GestureClassification (token, c_gesture, requires_gaze_target)

    alt FIST (REST) token detected
        ARB->>ARB: NO_ACTION — Midas Touch guard active, block Layer 3
    else keyboard_active within 800ms
        ARB->>ARB: KEYBOARD mode — suppress gesture evaluation
    else mouse_active within 600ms
        ARB->>L3A: MOUSE_PRIORITY — c_gesture_eff = c_gesture * 0.60
    else Gesture mode clear
        ARB->>L3A: Passes full GestureClassification unchanged
    end

    DB->>L3A: Provides [w_gaze, w_head], θ_a, α, dwell thresholds (Profile v_k)
    L3A->>L3A: A1: c_target = w_gaze·s_gaze + w_head·s_head; gate: dwell_ms ≥ τ_dwell
    L3A->>L3A: A2: gate: c_gesture ≥ θ_gesture AND stable_ms ≥ 80ms (Tier 0)
    L3A->>L3A: A3: S_a = α·c_target + (1-α)·c_gesture if requires_gaze_target else c_gesture
    L3A->>L3B: Composed Command Candidate (command, gaze_anchor, S_a) if S_a ≥ θ_a

    alt Tier 0 fails (gesture not stable 80ms)
        L3B->>L3B: Drops candidate — intentionality gate not met
    else Tier 1 Action (Safe / Continuous)
        L3B->>OS: Direct instant dispatch
    else Tier 2 Action (Destructive)
        L3B->>L3B: Evaluates User-Relative Gate θ_tier2,a & runs 600ms visual dwell
        L3B->>OS: Dispatches on dwell completion
    end

    alt Focused element is text input field (UIAutomation check)
        OS->>OS: Enters KEYBOARD_HANDOFF mode — gesture eval paused
        OS->>User: Shows "Keyboard Active" HUD indicator
    else Standard action dispatch
        OS->>L4: Action executed; pushes ActionContext to Queue (dispatched_at = t0)
    end

    Note over User,L4: Temporal Observation Window [t0 + 200ms, t0 + 1.8s]

    alt User Reverses Action (e.g., Ctrl+Z / Oppositional Swipe within 800ms)
        User->>L4: Triggers corrective action (Δt = 800ms)
        L4->>L5: Emits FeedbackEvent(outcome = -1, c_fb = 0.53, failure = FALSE_ACTIVATION)
    else No Reversal within 1.8s (Stability Expiration)
        L4->>L5: Emits FeedbackEvent(outcome = +1, c_fb = 1.0, failure = NONE)
    end

    L5->>L5: Computes Health Metrics (EWMA AG, WSI, ACI, ECE, SPRT)
    L5->>L5: Evaluates Multi-Criteria Gatekeeper (Drift, Contradiction, Noise, Samples)

    alt Gatekeeper Verdict: APPROVE
        L5->>L6: Emits Validated Learning Signal (e_a, g_weight, c_fb)
        L6->>L6: Executes Decoupled SGD on [w_gaze, w_head], θ_a, α, τ_dwell
        L6->>L6: Applies Box-Constrained Simplex Projection (w_i ∈ [0.05, 0.85])
        L6->>DB: Increments version & writes ProfileSnapshot (Profile v_k+1)
    else Gatekeeper Verdict: REJECT
        L5->>L6: Drops update; logs LearningRecord(verdict = REJECT, reason)
    end
```

---

## 4. Global Uncertainty & Confidence Propagation Model

Uncertainty is modeled continuously across all architectural layers to govern parameter step sizes and validation thresholds:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         GLOBAL UNCERTAINTY PROPAGATION PIPELINE                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [1. Perceptual Uncertainty (Layer 1)]                                                           │
│      σ_perceptual² = w_aᵀ · Σ_sensor · w_a   (Propagated sensor covariance)                      │
│                                                                                                  │
│  [2. Decision Margin / Epistemic Distance (Layer 3)]                                             │
│      Δ_decision = |S_a(x) - θ_a|                                                                 │
│      g_weight(Δ_decision) = 1 / (1 + exp(-40(Δ_decision - 0.05))) (Ambiguity Gate)              │
│                                                                                                  │
│  [3. Supervisory Feedback Confidence (Layer 4)]                                                  │
│      c_fb(Δt) = exp(-(Δt - 0.20) / τ_user)                                                       │
│                                                                                                  │
│  [4. System Historical Health (Layer 5)]                                                         │
│      H_system = (1 - ECE_t) · ACI_t                                                              │
│                                                                                                  │
│  [5. Unified Global Update Confidence (Layer 6)]                                                 │
│      C_update = (1 / (1 + σ_perceptual)) · g_weight(Δ_decision) · c_fb(Δt) · H_system            │
│                                                                                                  │
│  [Effective Learning Rate Modulation]:                                                           │
│      η_eff(t) = η_0 · C_update   (Dynamically modulates SGD step size)                           │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Layer 1: Perception & Multimodal Feature Extraction

### 5.1 Modality Extractors
1. **Ocular Gaze & Iris Tracking**:
   - MediaPipe FaceMesh extracts 468 facial mesh landmarks and 10 iris landmarks (468–477).
   - Computes normalized pupil offsets relative to eye corner baselines:
     $$r_{\text{iris}, x} = \frac{x_{\text{iris}} - x_{\text{inner}}}{x_{\text{outer}} - x_{\text{inner}}}, \quad r_{\text{iris}, y} = \frac{y_{\text{iris}} - y_{\text{superior}}}{y_{\text{inferior}} - y_{\text{superior}}}$$
   - Confidence $s_{\text{gaze}} \in [0, 1]$ is gated by Eye Aspect Ratio ($\text{EAR} \ge 0.18$).

2. **Head Pose Orientation (SolvePnP)**:
   - 6 canonical 3D facial feature points mapped to 2D image plane via camera intrinsic matrix $\mathbf{K}$.
   - Solves Levenberg-Marquardt Perspective-n-Point optimization to obtain continuous Euler angles: Yaw $(\psi)$, Pitch $(\theta)$, Roll $(\phi)$.
   - Confidence $s_{\text{head}} \in [0, 1]$ is derived via Mahalanobis distance from calibrated neutral posture.

3. **Hand Kinematics & Gesture Syntax**:
   - MediaPipe Hands extracts 21 3D landmarks.
   - Computes normalized pinch distance $d_{\text{pinch}}$, palm normal vector $\mathbf{n}_{\text{palm}}$, and wrist velocity $\mathbf{v}_{\text{wrist}}(t)$.

### 5.2 Adaptive Holt-Winters Exponential Smoothing Filter
Eliminates high-frequency landmark jitter during stationary dwell while eliminating lag during rapid motion:
$$\hat{x}_t = \alpha_t x_t + (1 - \alpha_t)(\hat{x}_{t-1} + b_{t-1}), \quad b_t = \beta (\hat{x}_t - \hat{x}_{t-1}) + (1 - \beta) b_{t-1}$$
where dynamic smoothing coefficient $\alpha_t = \text{clip}(\alpha_0 + \gamma \|\mathbf{v}_{\text{wrist}}(t)\|, 0.20, 0.85)$.

### 5.3 Gaze Dwell Tracker Sub-Module
Tracks temporal gaze fixation to distinguish intentional target acquisition from passive gaze-overs during reading or idle attention. Operates within Layer 1's per-frame loop with negligible overhead ($<0.3$ ms).

**Inputs**: Smoothed screen coordinates $(u_t, v_t)$ from the affine gaze mapping pipeline.

**Computations per frame**:
$$\sigma^2_{\text{dwell},t} = \frac{1}{W}\sum_{k=0}^{W-1}\left[(u_{t-k}-\bar{u})^2 + (v_{t-k}-\bar{v})^2\right], \quad W = \lceil 0.15 \cdot \text{FPS}\rceil \approx 5 \text{ frames}$$
$$\text{gaze\_stability}_t = \exp\!\left(-\frac{\sigma^2_{\text{dwell},t}}{R^2}\right), \quad R = 40\text{ px (fixation radius)}$$
$$\text{gaze\_dwell\_ms}_t = \text{consecutive frames where } \|(u_t,v_t)-(u_{\text{anchor}},v_{\text{anchor}})\| \le R \;\times\; \Delta t_{\text{frame}}$$

**Outputs appended to feature vector**:
- `gaze_dwell_ms`: Continuous dwell duration in milliseconds on the current spatial anchor.
- `gaze_stability`: Spatial stability score $\in [0,1]$ over the last 150 ms window.
- `gaze_anchor`: Declared valid screen coordinate $(u_{\text{anchor}}, v_{\text{anchor}})$ when `gaze_dwell_ms >= profile.gaze_target_dwell_ms` (personalized per user, default 80 ms).

**Gate contract to Layer 3A Stage A1**: A gaze coordinate is accepted as a valid spatial targeting input only when `gaze_dwell_ms >= profile.gaze_target_dwell_ms`. This eliminates false activations from incidental gaze-overs during reading.

---

## 5A. Layer 1B: Gesture Classifier & Vocabulary Engine

Positioned between Layer 1 (raw perception) and the Modality Arbiter, Layer 1B translates continuous kinematic signals into discrete, semantically named gesture tokens with associated recognition confidences. It is the formal boundary between raw signal processing and semantic command interpretation. The gesture vocabulary is **designer-fixed and version-controlled**; the adaptive engine personalizes only the per-user recognition thresholds, never the semantic mapping.

### 5A.1 Gesture Token Dictionary

| Gesture Token | Detection Condition | `requires_gaze_target` |
|---|---|---|
| `PINCH` | $d_{\text{pinch}} < \theta_{\text{pinch}}$ sustained $\ge 1$ frame | True |
| `PINCH_DOUBLE` | Two `PINCH` events within 400 ms | True |
| `PINCH_HOLD` | $d_{\text{pinch}} < \theta_{\text{pinch}}$ sustained $\ge 300$ ms | True |
| `OPEN_PALM` | All 5 finger extension scores $> 0.80$, palm normal facing camera | True |
| `SWIPE_LEFT` | $v_{\text{wrist},x} < -\theta_{\text{vel}}$ sustained $\ge 80$ ms | False |
| `SWIPE_RIGHT` | $v_{\text{wrist},x} > +\theta_{\text{vel}}$ sustained $\ge 80$ ms | False |
| `SWIPE_UP` | $v_{\text{wrist},y} < -\theta_{\text{vel}}$ sustained $\ge 80$ ms | False |
| `SWIPE_DOWN` | $v_{\text{wrist},y} > +\theta_{\text{vel}}$ sustained $\ge 80$ ms | False |
| `TWO_FINGER_SPREAD` | $\Delta d_{\text{index-middle}} > +\theta_{\text{spread}}$ per frame | False |
| `TWO_FINGER_PINCH` | $\Delta d_{\text{index-middle}} < -\theta_{\text{spread}}$ per frame | False |
| `THUMBS_UP` | Thumb extended, fingers 2-5 curled $>0.75$ | False |
| `FIST` | All finger curl scores $> 0.80$ — **REST / NO-ACTION guard token** | N/A |
| `NONE` | No classifiable gesture pattern detected | N/A |

### 5A.2 Gesture-to-Action Semantic Table (Designer-Fixed)

| Gesture Token | OS Action Dispatched |
|---|---|
| `PINCH` + gaze target | `LEFT_CLICK` at $(u_{\text{anchor}}, v_{\text{anchor}})$ |
| `PINCH_DOUBLE` + gaze target | `DOUBLE_CLICK` at $(u_{\text{anchor}}, v_{\text{anchor}})$ |
| `PINCH_HOLD` + gaze target | `DRAG_START` from $(u_{\text{anchor}}, v_{\text{anchor}})$ |
| `OPEN_PALM` + gaze target | `RIGHT_CLICK` at $(u_{\text{anchor}}, v_{\text{anchor}})$ |
| `SWIPE_LEFT` | `NAVIGATE_BACK` (Alt+Left) |
| `SWIPE_RIGHT` | `NAVIGATE_FORWARD` (Alt+Right) |
| `SWIPE_UP` | `SCROLL_UP` |
| `SWIPE_DOWN` | `SCROLL_DOWN` |
| `TWO_FINGER_SPREAD` | `ZOOM_IN` (Ctrl++) |
| `TWO_FINGER_PINCH` | `ZOOM_OUT` (Ctrl+-) |
| `THUMBS_UP` | `CONFIRM` (Enter key) |
| `FIST` | `NO_ACTION` (REST guard — Midas Touch prevention) |
| `NONE` | `NO_ACTION` |

### 5A.3 Recognition Confidence Score

$$c_{\text{gesture}} = \text{sigmoid}\!\left(k_s \cdot \left(d_{\text{margin}} - d_{\text{threshold}}\right)\right), \quad k_s = 20$$

where $d_{\text{margin}}$ is the signed distance of the primary kinematic feature from its classification boundary. This confidence feeds into Layer 3A Stage A2 and Layer 5's gatekeeper.

### 5A.4 Output Contract

```python
@dataclass
class GestureClassification:
    gesture_token: str          # Token from vocabulary table above
    c_gesture: float            # Recognition confidence in [0, 1]
    requires_gaze_target: bool  # True if action needs a screen coordinate
    action_intent: str          # Mapped OS action string (from semantic table)
    stable_duration_ms: float   # How long this token has been continuously held
```

---

## 5B. Active Modality Arbiter

The Modality Arbiter is a lightweight pre-Layer-3 gating component that monitors concurrent physical device activity and determines whether gesture evaluation should proceed, be suppressed, or be soft-reduced. It elevates mouse and keyboard signals from reactive correction evidence (Layer 4 Sub-Detector 5) to proactive gating conditions before any action can be composed or fired.

### 5B.1 Device Activity Monitor

The Arbiter maintains three rolling activity flags polled asynchronously at 30 Hz via the OS hook already installed for Layer 4:

| Flag | Condition | Window |
|---|---|---|
| `keyboard_active` | Any keystroke detected | Last 800 ms |
| `mouse_active` | Mouse velocity $> 200$ px/s | Last 600 ms |
| `mouse_clicking` | Any mouse button pressed | Last 300 ms |

### 5B.2 Arbitration Decision Logic

```
IF gesture_token == FIST:
    Emit: DEVICE_MODE = NO_ACTION
    Reason: REST state — Midas Touch prevention guard
    Action: Block Layer 3 evaluation entirely for this frame

ELIF keyboard_active:
    Emit: DEVICE_MODE = KEYBOARD
    Reason: Physical keyboard in active use — no parallel gesture intent
    Action: Suppress gesture evaluation; pass keyboard events unchanged

ELIF mouse_active OR mouse_clicking:
    Emit: DEVICE_MODE = MOUSE_PRIORITY
    Reason: Physical pointing device active — soft confidence reduction
    Action: c_gesture_effective = c_gesture * 0.60

ELSE:
    Emit: DEVICE_MODE = GESTURE
    Reason: No conflicting device activity — full gesture pipeline active
    Action: Pass GestureClassification unchanged to Layer 3
```

### 5B.3 Relationship to Layer 4 Sub-Detector 5

Layer 4 Sub-Detector 5 (`Physical Input Override`) remains operational as a post-hoc fallback for misfire cases that slip through the Arbiter's rolling windows. The Arbiter and Sub-Detector 5 are complementary: the Arbiter **prevents** misfires proactively; Sub-Detector 5 **corrects** the residual cases reactively. They are not redundant.

---


## 6. Layer 2: Calibration & Profile Bootstrapping Wizard

A 60–90 second interactive onboarding protocol (10–15 sample interactions) bootstraps the initial profile (`Profile v1`):

```
┌────────────────────────────────────────────────────────────────────────┐
│               5-PHASE INTERACTIVE CALIBRATION TIMELINE                 │
├────────────────────────────────────────────────────────────────────────┤
│  Phase A: System & Lighting Readiness (0–10s, 1 sample)                │
│  Phase B: Neutral Head Pose & Motion Range (10–25s, 3 samples)         │
│  Phase C: 5-Point Ocular Gaze Mapping (25–50s, 5 samples)              │
│  Phase D: Gesture Kinematics & Tempo Baseline (50–75s, 4 samples)      │
│  Phase E: Profile Synthesis & Initial Weighting (75–90s, automated)   │
└────────────────────────────────────────────────────────────────────────┘
```

### Mathematical Formulations
1. **Neutral Posture 95% Confidence Ellipsoid**:
   $$\mathcal{E}_{\text{head}} = \left\{ \mathbf{p} \in \mathbb{R}^3 \mid (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}})^T \boldsymbol{\Sigma}_{\text{pose}}^{-1} (\mathbf{p} - \boldsymbol{\mu}_{\text{pose}}) \le \chi^2_3(0.95) \approx 7.815 \right\}$$
2. **5-Point Gaze 2D Affine Perspective Mapping**:
   $$\begin{bmatrix} u_{\text{screen}} \\ v_{\text{screen}} \end{bmatrix} = \mathbf{M}_{\text{gaze}} \begin{bmatrix} r_{\text{iris}, x} \\ r_{\text{iris}, y} \\ 1 \end{bmatrix} + \begin{bmatrix} \Delta x_{\text{offset}} \\ \Delta y_{\text{offset}} \end{bmatrix}$$
3. **Personal Reaction Tempo Baseline ($\tau_{\text{user}}$)**:
   $$\tau_{\text{user}} = \text{clip}\left(0.60 \cdot \frac{T_{\text{user\_tempo}}}{0.80\text{s}}, \ 0.35\text{s}, \ 0.95\text{s}\right)$$
4. **Variance-Informed Weight Initialization**:
   $$\tilde{w}_i^{(0)} = \frac{1 / \sigma_i^2}{\sum_{j \in \{\text{gaze}, \text{head}, \text{hand}\}} 1 / \sigma_j^2} \implies \mathbf{w}_a^{(0)} = \text{BoxSimplexProjection}(\tilde{\mathbf{w}}^{(0)}, \mathbf{l}=0.05\cdot\mathbf{1}, \mathbf{u}=0.85\cdot\mathbf{1})$$
   *(Compensates for sensor limitations: noisy gaze from thick glasses begins with lower initial weight $w_{\text{gaze}}=0.20$, compensated by hand $w_{\text{hand}}=0.55$).*

---

## 7. Layer 3: Weighted Decision Engine & Safety Reasoning

Layer 3 is internally partitioned into three decoupled sub-stages:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LAYER 3 INTERNAL SUB-STAGES                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [Feature Vector x]                                                    │
│        │                                                               │
│        ▼                                                               │
│  ┌──────────────────────────────────────────────┐                      │
│  │ Stage 3A: Confidence Fusion & Intent Evaluator│                      │
│  │ • S_a(x) = w_gaze·s_gaze + w_head·s_head +   │                      │
│  │            w_hand·s_hand                     │                      │
│  │ • Evaluates base condition: S_a(x) ≥ θ_a     │                      │
│  └──────────────────────┬───────────────────────┘                      │
│                         │ (Intent Candidate)                           │
│                         ▼                                              │
│  ┌──────────────────────────────────────────────┐                      │
│  │ Stage 3B: Post-Decision Safety Reasoning     │                      │
│  │ • Determines Action Tier (Tier 1 vs Tier 2)  │                      │
│  │ • Tier 2 Gate: S_a ≥ min(0.95, max(θ_a+0.15, │                      │
│  │                           μ_S + 1.5σ_S))     │                      │
│  │ • Manages 600ms HUD visual dwell confirmation│                      │
│  │ • Arms 3.0s Grace-Period Undo Hook Stack     │                      │
│  └──────────────────────┬───────────────────────┘                      │
│                         │ (Approved for Execution)                     │
│                         ▼                                              │
│  ┌──────────────────────────────────────────────┐                      │
│  │ Stage 3C: OS Execution & Context Dispatch    │                      │
│  │ • Executes native OS API (pyautogui / win32) │                      │
│  │ • Pushes immutable ActionContext to Layer 4  │                      │
│  └──────────────────────────────────────────────┘                      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Layer 4: Implicit Feedback Observer & Temporal State Machine

Monitors post-action user behavior to infer supervisory labels without explicit user queries:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         IMPLICIT FEEDBACK TEMPORAL STATE MACHINE                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [t0: Action Executed & Logged to ActionContextQueue]                                            │
│         │                                                                                        │
│         ▼                                                                                        │
│  ┌──────────────────────────────────────────────────────────┐                                    │
│  │ Window 1: REFRACTORY WINDOW [t0, t0 + 200ms]             │ ──► Events Ignored (Motor Delay)   │
│  └──────────────────────────┬───────────────────────────────┘                                    │
│                             ▼                                                                    │
│  ┌──────────────────────────────────────────────────────────┐                                    │
│  │ Window 2: CORRECTION WINDOW [t0 + 200ms, t0 + 1.8s]      │                                    │
│  │                                                          │                                    │
│  │  • Sub-Detector 1: Global OS Undo (Ctrl+Z, Alt+Left)     │ ──► Emits IMPLICIT_NEG             │
│  │  • Sub-Detector 2: Directional Oppositional Reversal     │     with Continuous Confidence:    │
│  │  • Sub-Detector 3: Rapid Duplicate Gesture Retries       │     c_fb = exp(-(Δt - 0.2)/τ_user) │
│  │  • Sub-Detector 4: Immediate App/Tab Dismissal           │                                    │
│  │  • Sub-Detector 5: Manual Physical Mouse/Key Override    │                                    │
│  └──────────────────────────┬───────────────────────────────┘                                    │
│                             ▼ (No Negative Event Detected)                                       │
│  ┌──────────────────────────────────────────────────────────┐                                    │
│  │ Window 3: STABILITY EXPIRATION [t > t0 + 1.8s]           │ ──► Emits IMPLICIT_POS             │
│  │           (Action Persisted Without Reversal)            │     with Confidence c_fb = 1.0     │
│  └──────────────────────────┬───────────────────────────────┘                                    │
│                             ▼                                                                    │
│  [Action Context Resolved & Pruned from Queue]                                                   │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 8.1 The Five Asynchronous Negative Sub-Detectors
1. **Global OS Undo Hook**: Low-level hook capturing `Ctrl+Z`, `Alt+Left`, `Ctrl+Shift+T` on matching active window PID $\implies$ `IMPLICIT_NEG` (`FALSE_ACTIVATION`).
2. **Directional Oppositional Reversal**: Detects immediate inverse continuous commands (Scroll Down $\to$ Scroll Up within 1.0s) $\implies$ `IMPLICIT_NEG` (`WRONG_TARGET`).
3. **Rapid Duplicate Gesture Retries**: Same gesture repeated $\ge 2$ times in 1.2s without system trigger $\implies$ `IMPLICIT_NEG` (`FALSE_REJECTION`).
4. **Immediate Window/Tab Dismissal**: Newly launched window closed within 1.5s via `Alt+F4` / `Ctrl+W` / Close Button $\implies$ `IMPLICIT_NEG` (`FALSE_ACTIVATION`).
5. **Physical Input Override**: Sudden physical mouse movement ($>800\text{px/s}$) or keyboard navigation within 1.0s $\implies$ `IMPLICIT_NEG` (`USER_OVERRIDE`).

---

## 9. Layer 5: Runtime Assessment Engine (RAE)

Layer 5 is decomposed into two internal engines:

```
┌────────────────────────────────────────────────────────────────────────┐
│               LAYER 5: RUNTIME ASSESSMENT ENGINE (RAE)                 │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ENGINE 5A: RUNTIME METRICS ENGINE                                │  │
│  │ • Computes EWMA Adaptation Gain (AG_t, α=0.10)                   │  │
│  │ • Computes Sliding Learning Velocity (LV_t, W=20)                │  │
│  │ • Computes Weight Stability Index (WSI_t)                        │  │
│  │ • Computes Adaptation Confidence Index (ACI_t)                   │  │
│  │ • Computes Expected Calibration Error (ECE_t)                    │  │
│  │ • Computes Recovery Rate (RR) & Drift Recovery Time (DRT)        │  │
│  └──────────────────────────────────┬───────────────────────────────┘  │
│                                     │ Live Health Metrics Snapshot      │
│                                     ▼                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ ENGINE 5B: DECISION & LEARNING VALIDATOR (GATEKEEPER)            │  │
│  │ • Validates Sample Count Floor (k ≥ 3)                           │  │
│  │ • Validates Continuous Feedback Confidence (c_fb ≥ 0.40)         │  │
│  │ • Enforces Macro Drift Lockout (Blocks updates if S_m ≥ 2.89)    │  │
│  │ • Resolves Sub-Detector Contradictions                           │  │
│  │ • Evaluates Environmental Sensor SNR (Lux > 20, GazeVar < 0.25)  │  │
│  │ • Emits: APPROVE vs REJECT Verdict + Validated Signal            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 9.1 Categorized Health Metrics Taxonomy

| Category | Metric | Mathematical Formulation | Direct System & Decision Impact |
|---|---|---|---|
| **Learning Quality** | **EWMA Adaptation Gain ($AG_t$)** | $AG_t = \alpha (\text{Acc}_t - \text{Base}) + (1-\alpha) AG_{t-1}$ <br> ($\alpha = 0.10$, $\text{Base} = \text{Initial Accuracy}$) | • Transitions HUD from `LEARNING` $\to$ `IMPROVING` when $AG_t > 0.05$. <br> • Gatekeeper requires $AG_t > 0.05$ to declare true parameter convergence. |
| **Learning Quality** | **Sliding Learning Velocity ($LV_t$)** | $LV_t = \frac{\text{Error}(t-W) - \text{Error}(t)}{W}$ <br> ($W = 20$ interaction window) | • Modulates dynamic learning rate $\eta(t) = \eta_0 / (1 + \lambda \cdot LV_t)$. <br> • Signals acceleration ($LV_t > 0$) vs. plateauing ($LV_t \approx 0$). |
| **Model Stability** | **Weight Stability Index ($WSI_t$)** | $WSI_t = \frac{1}{d} \sum_{i=1}^d \sqrt{\frac{1}{K}\sum_{k=0}^{K-1} (w_{i, t-k} - \bar{w}_i)^2}$ <br> ($K = 30$, $d = 3$) | • When $WSI_t < 0.02$, weights are declared stable. <br> • Prevents parameter thrashing by dampening SGD learning rate. |
| **Model Stability** | **Adaptation Confidence Index ($ACI_t$)** | $ACI_t = \text{clip}\left(0.30 \frac{\min(N_a, 20)}{20} + 0.30 (1 - \frac{WSI_t}{0.10}) + 0.25 \frac{AG_t}{0.20} - 0.15 ECE_t, 0, 1\right)$ | • Renders live health score on HUD/Dashboard. <br> • $ACI_t \ge 0.75$ triggers the `STABLE` state badge. |
| **System Reliability**| **Expected Calibration Error ($ECE_t$)** | $ECE_t = \sum_{b=1}^{B} \frac{|B_b|}{N} \left| \text{Acc}(B_b) - \text{Conf}(B_b) \right|$ <br> ($B = 10$ confidence bins) | • Penalizes overconfident/underconfident models. <br> • Influences $ACI_t$ and adjusts visual dwell confidence ring. |
| **System Reliability**| **Recovery Rate ($RR$)** | $RR = \frac{\sum \mathbb{I}(\text{Outcome}_{t+1} = \text{Success} \mid \text{Outcome}_t = \text{Error})}{\sum \mathbb{I}(\text{Outcome}_t = \text{Error})}$ | • Evaluates UI resilience and user error recovery fluency. <br> • Emitted in Session Report executive benchmark table. |
| **Robustness** | **Drift Recovery Time ($DRT$)** | $DRT = t_{\text{stabilized}} - t_{\text{alarm}}$ <br> (Time from Wald SPRT $S_m \ge 2.89$ to reset $S_m \le -2.25$) | • Quantifies framework agility under environmental changes (e.g. lighting shifts, posture movement). |

---

## 10. Layer 6: Online Parameter Updater & Dual-Scale Optimizer

### 10.1 Micro-Adaptation (Per-Interaction SGD)
When Layer 5 emits `APPROVE`, parameters are updated via ambiguity-gated Stochastic Gradient Descent:
$$\tilde{\mathbf{w}}_a^{(t+1)} = \mathbf{w}_a^{(t)} + \eta_w(t) \cdot g_{\text{weight}}(S_a, \theta_a) \cdot c_{fb} \cdot e_a \cdot \mathbf{x}$$
$$\theta_a^{(t+1)} = \text{clip}\left(\theta_a^{(t)} - \eta_\theta(t) \cdot c_{fb} \cdot e_a, \ 0.35, \ 0.85\right)$$
where $g_{\text{weight}}(S_a, \theta_a) = \frac{1}{1 + \exp(-40 (|S_a - \theta_a| - 0.05))}$.

#### Exact 1D Bisection Box-Constrained Simplex Projection
Guarantees $\sum_{i=1}^3 w_{a, i} = 1.0$ and $w_{a, i} \in [0.05, 0.85]$ via dual bisection:
$$\mathbf{w}_a^{(t+1)} = \text{clip}(\tilde{\mathbf{w}}_a^{(t+1)} - \mu^* \mathbf{1}, \ 0.05, \ 0.85) \quad \text{such that } \sum_{i=1}^3 w_{a, i}^{(t+1)} = 1.0$$

### 10.2 Algorithmic Macro-Adaptation (Periodic Epoch State Machine)
Executes every $N=30\text{--}50$ interactions:
1. **Statistical Aggregation**: Computes running parameters ($\mu_{S, a}, \sigma_{S, a}$) and ECE.
2. **Trend & Covariance Analysis**: Evaluates $\text{Cov}(\mathbf{w}_t, \mathbf{w}_{t-K})$.
3. **Macro Policy Decisions**:
   - `MERGE`: Commits micro-updates into baseline if $AG_t > 0.05 \land WSI_t < 0.02 \land ECE_t < 0.10$.
   - `FREEZE`: Locks baseline weights and lowers $\eta \to \eta_{\min}$ if $ACI_t \ge 0.80 \land WSI_t < 0.01$.
   - `DISCARD`: Rolls back parameter drift to previous snapshot if $ECE_t$ spikes $>0.15$ or $AG_t < -0.05$.
   - `RECALIBRATE`: Locks micro-updates and alerts user for a 30s recalibration if Wald SPRT $S_m \ge 2.89$.
4. **Snapshot Serialization**: Persists versioned `ProfileSnapshot` (`Profile v_k+1`).

---

## 11. Telemetry Schemas & Diagnostics

### 11.1 `ProfileSnapshot` Schema
```python
@dataclass
class ProfileSnapshot:
    user_id: str
    version_id: int
    timestamp_epoch: float
    session_id: str
    is_session_boundary: bool
    modality_weights: dict          # {action: [w_gaze, w_head, w_hand]} (∑w_i = 1.0)
    action_thresholds: dict         # {action: θ_a ∈ [0.35, 0.85]}
    gaze_calibration_matrix: list   # 2x3 affine matrix M_gaze
    neutral_pose_mean: list         # [μ_yaw, μ_pitch, μ_roll]
    neutral_pose_cov_inv: list      # 3x3 inverted covariance matrix Σ_pose⁻¹
    user_latency_tempo_tau: float   # Calibrated decay constant τ_user
    running_score_stats: dict       # {action: {"mean": μ_S, "std": σ_S, "count": N}}
    adaptation_confidence_index: float # ACI ∈ [0.0, 1.0]
    weight_stability_index: float      # WSI score
    expected_calibration_error: float  # ECE score
    cumulative_adaptation_gain: float  # Cumulative AG
    total_interactions_seen: int
    total_updates_approved: int
    total_updates_rejected: int
    failure_counts_by_taxonomy: dict
    wald_sprt_score: float
    last_recalibration_timestamp: float
    recalibration_count: int
    baseline_ambient_lux: float
    baseline_user_distance_mm: float

    # NEW FIELDS — Gesture Vocabulary, Command Composer & Modality Arbiter
    gesture_thresholds: dict
    # Per-token recognition thresholds, personalized per user.
    # Example: {"PINCH": {"d_pinch_max": 0.045, "sustain_ms": 80},
    #            "OPEN_PALM": {"extension_min": 0.82},
    #            "SWIPE": {"velocity_min": 0.35, "sustain_ms": 80}}

    rest_pose_signature: dict
    # Learned FIST / resting hand landmark geometry for this user.
    # Stored as 21 normalized 3D landmark coordinates captured during Phase D calibration.

    intentionality_dwell_ms: float
    # Tier 0 stability gate. Gesture must be held this long before evaluation.
    # Range: [50, 200] ms. Adapted via macro epoch. Default: 80 ms.

    gaze_target_dwell_ms: float
    # Minimum gaze fixation duration before coordinate is accepted as a valid target.
    # Range: [60, 250] ms. Adapted via macro epoch. Default: 80 ms.

    command_composer_alpha: float
    # Spatial-intent balance weight alpha in Stage A3. Range: [0.30, 0.70].
    # Higher alpha = gaze-dominant (precise gaze user).
    # Lower alpha = gesture-dominant (tremor or thick corrective lenses).

    modality_weights_spatial: dict
    # {action: [w_gaze, w_head]} — spatial resolution weights for Stage A1.
    # Replaces the legacy three-way modality_weights for gaze+head targeting.
    # w_hand entry is retired; gesture confidence is now sourced from Layer 1B.

    text_input_mode: str
    # "keyboard_handoff" — UIAutomation text field detection (Option A, recommended).
    # "virtual_keyboard" — on-screen keyboard for assistive technology contexts (Option B).


### 11.2 4-Stage Failure Governance Subsystem
1. **Stage 1 (Detection)**: 5 asynchronous negative sub-detectors.
2. **Stage 2 (Classification)**: 7 failure modes (`FALSE_ACTIVATION`, `FALSE_REJECTION`, `WRONG_TARGET`, `LOW_CONFIDENCE`, `DELAYED_RESPONSE`, `USER_OVERRIDE`, `ENVIRONMENTAL_DRIFT`).
3. **Stage 3 (Severity Scoring)**: Level 1 (Benign continuous over-reach) to Level 5 (Critical state-altering misfire).
4. **Stage 4 (Targeted Corrective Action Policy)**: Modulates parameter updates, threshold margins, and dwell confirmation based on specific failure diagnoses.

---

## 12. Computational Budgets & Latency Performance

| Pipeline Stage | Latency Budget (Target) | Optimization Strategy |
|---|---|---|
| Camera Ingestion (1080p @ 30 FPS) | $< 5.0\text{ ms}$ | Decoupled background capture thread with lock-free ring buffer |
| MediaPipe FaceMesh & Hand Tracking | $< 18.0\text{ ms}$ | Multi-process worker pool, lightweight BlazeFace / BlazeHand models |
| SolvePnP Head Pose Estimation | $< 2.0\text{ ms}$ | Levenberg-Marquardt iterative solver on 6 canonical landmarks |
| Spatial-Temporal Smoothing Buffer | $< 0.5\text{ ms}$ | Vectorized NumPy Holt-Winters exponential filter |
| Layer 3 Confidence Fusion & Safety Gate | $< 0.5\text{ ms}$ | Vectorized dot product $S_a = \mathbf{w}_a^T \mathbf{x}$ |
| Layer 4 Feedback Observer Check | $< 1.0\text{ ms}$ | Asynchronous OS event queue polling |
| Layer 5 Runtime Assessment (Metrics + Gate) | $< 1.5\text{ ms}$ | Vectorized sliding window variance and EWMA filter |
| Layer 6 SGD Update + Simplex Projection | $< 1.0\text{ ms}$ | Exact 1D dual bisection root finding ($<15$ iterations) |
| **Total End-to-End Latency** | **$< 29.5\text{ ms}$** | **Guarantees seamless 30 FPS real-time operation on CPU** |

---

## 13. Related Canonical Documentation & Spiral SDLC Lifecycle

This Architecture Specification interfaces directly with the master documentation and engineering lifecycle suite:
* **[Project Proposal](file:///d:/HCI/adaptive-multimodal-hci-proposal.md)**: Scientific motivation, RQ1–RQ4 framing, and academic contributions.
* **[ISO/IEC/IEEE 29148 SRS](file:///d:/HCI/adaptive-multimodal-hci-srs.md)**: Formal requirements specification and invariant acceptance criteria.
* **[Project Deliverables Specification](file:///d:/HCI/adaptive-multimodal-hci-deliverables.md)**: Detailed specifications for deliverables D1–D5, E1–E3, and DOC1–DOC5.
* **[Spiral SDLC Methodology Specification](file:///d:/HCI/adaptive-multimodal-hci-sdlc-spiral.md)**: Risk-driven 7-spiral development model mapping the 6 layers to iterative verification cycles.
* **[Base Repository Structure Specification](file:///d:/HCI/adaptive-multimodal-hci-repo-structure.md)**: Complete directory structure and module layout.
* **[Project Implementation Plan](file:///d:/HCI/adaptive-multimodal-hci-implementation-plan.md)**: 4-week execution roadmap and empirical protocols.
