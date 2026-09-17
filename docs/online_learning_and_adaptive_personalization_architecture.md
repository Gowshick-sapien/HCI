# Online Learning and Adaptive Personalization Architecture

## Executive Summary

The Multimodal Human-Computer Interaction (HCI) platform incorporates a safety-gated, closed-loop, dual-scale dynamic adaptation engine. Rather than relying on static heuristic rules or unconstrained deep-learning retraining in the wild, the system continuously evaluates real-time user interactions, extracts implicit supervisory feedback, validates systematic drift through statistical hypothesis testing, and optimizes user-specific parameters across micro- and macro-timescales.

This document details the mathematical formulations, architectural layers, codebase implementation, and empirical training dynamics that govern how repeated testing on the Interactive Testbench Suite refines a user profile, reduces error rates, and maximizes operational efficiency.

---

## 1. Problem Formulation and Motivation

### 1.1 Non-Stationarity in Multimodal Human-Computer Interfaces
Standard multimodal interfaces combine eye gaze, head pose, and hand gestures using static weighting schemes (e.g., fixed linear combination or static decision trees). In production environments, these static architectures degrade due to three fundamental non-stationary factors:

1. **Neuromuscular Fatigue and Saccadic Jitter**: As user sessions progress, ocular fixation stability declines and involuntary micro-saccades increase. A static gaze model calibrated at minute 0 exhibits severe spatial drift by minute 30.
2. **Inter-Subject Morphological Variance**: Users possess different ocular geometry (pupil-to-iris ratios), varying finger span and pinch kinematics, and distinct interaction tempos ($\tau$). A universal static threshold causes false activations ("Midas Touch") for fast users and missed triggers for deliberate users.
3. **Environmental Non-Stationarity**: Shifting ambient illumination alters camera contrast, affecting landmark localization quality.

### 1.2 The Failure of Naive Online Retraining
Attempting to fine-tune deep neural networks (e.g., MediaPipe or Vision Transformers) continuously at runtime causes:
- **Catastrophic Forgetting**: The network overfits to transient postures and loses general tracking capabilities.
- **Latency and Compute Spikes**: Model weight backpropagation exceeds the real-time 30-60 FPS execution budget.
- **Instability to Outliers**: Transient human noise (blinking, sneezing, temporary gaze diversions) corrupts model parameters.

### 1.3 The Closed-Loop Solution
The architecture addresses this through a **Decoupled 3-Tier Adaptation Model**:
- Deep perception networks remain frozen as robust feature extractors.
- Online adaptation is restricted to parametric fusion weights, threshold surfaces, dwell intervals, and calibration manifolds.
- All candidate parameter updates are gated through Wald's Sequential Probability Ratio Test (SPRT) to separate random noise from systematic bias.

---

## 2. High-Level Architectural Flow

```
 [Physical User Interaction]
  ├── Gaze Fixation & Saccades
  ├── Head Pose Euler Angles (Yaw, Pitch, Roll)
  ├── Hand Gesture Kinematics (13 Tokens)
  └── Hardware Events (Mouse Displacement, Keypresses)
               │
               ▼
 [Layer 1-3: Perception & Command Composition]
               │
       ┌───────┴────────────────────────┐
       ▼                                ▼
 [Execution Engine]       [Layer 4: Supervisory Feedback]
 (Testbench Targets)       ├── Implicit Mouse Takeover (USER_OVERRIDE)
       │                   ├── Keystroke Undos (Ctrl+Z, Esc, Backspace)
       │                   ├── Saccadic Escape (WRONG_TARGET)
       │                   └── Stability Expiration (IMPLICIT_POS >= 2.0s)
       │                                │
       ▼                                ▼
 [Interaction Telemetry] ──► [Layer 5: Dual-Scale Dynamic Adaptation]
                              ├── Engine 5A: Runtime Assessment (AssessmentEngine)
                              │   └── Computes EWMA Gain, ECE, Learning Velocity
                              ├── Engine 5B: Gatekeeper (SPRT Statistical Filter)
                              │   └── Approves/Rejects Updates via Wald Bounds
                              ├── Engine 5B: Micro-SGD Optimizer (MicroAdaptationEngine)
                              │   └── Simplex-Projected Online Gradient Descent
                              ├── Engine 5C: Macro Policy Machine (MacroAdaptationEngine)
                              │   └── Manages MERGE, FREEZE, DISCARD, RECALIBRATE
                              └── Persistent Storage: ProfileManager
                                  └── Atomic Serialization to data/profiles/{user_id}.json
```

---

## 3. Detailed Component Mechanisms

### 3.1 Layer 4: Supervisory Feedback Generation
Implemented in [implicit_detector.py](file:///d:/HCI/src/feedback/implicit_detector.py).

The system continuously evaluates post-action user behavior to infer ground-truth satisfaction without interrupting workflow:

1. **Mouse Takeover (`USER_OVERRIDE`)**:
   - Condition: Physical hardware mouse displacement $d \ge 16\text{ px}$ detected within a post-action window $t \in [0.20\text{ s}, 1.20\text{ s}]$.
   - Inference: The multimodal cursor placed the action incorrectly, forcing manual user intervention.
   - Confidence: $c = \max(0.60, \min(0.95, 1.0 - 0.40 \cdot (t / 1.20)))$.

2. **Keystroke Reversals (`FALSE_ACTIVATION` / `WRONG_TARGET`)**:
   - `Ctrl+Z` within $2.00\text{ s}$: Moderate severity reversal indicating an unintended action trigger.
   - `Escape` within $1.50\text{ s}$: Minor severity cancellation indicating wrong target selection.
   - `Backspace` within $1.20\text{ s}$: Input reversal indicating misdirected text focus.

3. **Saccadic Escape (`WRONG_TARGET`)**:
   - Condition: Gaze point abruptly jumps $>150\text{ px}$ away from the target within $0.40\text{ s}$ of action execution.
   - Inference: The user looked away in surprise from an erroneous target trigger.

4. **Stability Expiration (`IMPLICIT_POS`)**:
   - Condition: An action completes and remains uncontested for $\ge 2.00\text{ s}$ with no mouse takeover, reversal, or escape.
   - Inference: The action was intentional and successful, providing positive reinforcement.

---

### 3.2 Layer 5A: Runtime Assessment Engine
Implemented in [assessment_engine.py](file:///d:/HCI/src/adaptation/assessment_engine.py).

Maintains a sliding history window of $N = 30$ interactions and calculates statistical metrics:

1. **EWMA Adaptation Gain**:
   $$\Delta \text{Acc}_t = \text{Acc}_t - \text{Acc}_{t-1}$$
   $$\text{Gain}_t = \alpha \cdot \Delta \text{Acc}_t + (1 - \alpha) \cdot \text{Gain}_{t-1} \quad (\alpha = 0.15)$$

2. **Learning Velocity**:
   $$V = \frac{\|\mathbf{w}_t - \mathbf{w}_0\|_2}{\Delta t}$$
   Measures the rate of adaptation drift across the modality weight simplex.

3. **Weight Stability Index**:
   $$S_w = \text{clip}\left(1.0 - \frac{\sum_{i=1}^3 \text{Var}(w_i)}{\sigma^2_{\text{threshold}}}, 0.0, 1.0\right) \quad (\sigma^2_{\text{threshold}} = 0.04)$$

4. **Expected Calibration Error (ECE)**:
   Measures whether system confidence matches actual execution accuracy across $B = 5$ confidence bins:
   $$\text{ECE} = \sum_{b=1}^B \frac{|K_b|}{N} \left| \text{acc}(K_b) - \text{conf}(K_b) \right|$$

5. **System Health States**:
   - `BOOTSTRAPPING`: Sample count $< 8$.
   - `LEARNING`: Active adaptation with velocity $> 0.05$.
   - `IMPROVING`: Adaptation gain $> 0.02$ and accuracy $\ge 0.75$.
   - `STABLE`: Stability index $\ge 0.80$ and accuracy $\ge 0.80$.
   - `DRIFTING`: $\text{ECE} > 0.40$ and accuracy $< 0.40$.
   - `RECOVERING`: Regaining accuracy post-drift.

---

### 3.3 Layer 5B: SPRT Statistical Gatekeeper
Implemented in [gatekeeper.py](file:///d:/HCI/src/adaptation/gatekeeper.py).

To prevent adapting to transient noise, candidate updates must pass Wald's Sequential Probability Ratio Test:

- **Hypotheses**:
  - $H_0$: Error is random noise ($p_0 = 0.10$).
  - $H_1$: Error reflects systematic interaction drift ($p_1 = 0.60$).
- **Decision Bounds**:
  $$A = \log \left(\frac{1 - \beta}{\alpha}\right) \approx 2.89 \quad (\alpha = 0.05, \beta = 0.10)$$
  $$B = \log \left(\frac{\beta}{1 - \alpha}\right) \approx -2.25$$
- **Score Update**:
  $$\Lambda_n = \Lambda_{n-1} + c_{\text{confidence}} \cdot \log \left(\frac{P(x \mid H_1)}{P(x \mid H_0)}\right)$$
- **Logic**:
  - If $\Lambda_n \ge A$: Reject $H_0$, approve the update (`GatekeeperVerdict.APPROVE`).
  - If $\Lambda_n \le B$: Accept $H_0$, reset accumulator, reject update (`GatekeeperVerdict.REJECT`).
  - Otherwise: Indeterminate region; gather more evidence.

---

### 3.4 Layer 5B: Micro-SGD Online Gradient Descent
Implemented in [micro_adaptation.py](file:///d:/HCI/src/adaptation/micro_adaptation.py).

Upon Gatekeeper approval, the optimizer updates the modality fusion weights $\mathbf{w} = [w_{\text{eye}}, w_{\text{head}}, w_{\text{hand}}]^T$:

1. **Analytical Failure Gradients $\nabla_{\mathbf{w}} \mathcal{L}$**:
   - `WRONG_TARGET` (Gaze pointing error): $[+1.2, -0.6, -0.6]^T$ (Penalize eye, shift to head/hand).
   - `USER_OVERRIDE` (Mouse takeover): $[+0.4, -0.8, +0.4]^T$ (Penalize hand/eye, favor stable head pose).
   - `FALSE_ACTIVATION` (Spurious gesture): $[-0.5, -0.5, +1.0]^T$ (Penalize hand gesture weight).
   - `IMPLICIT_POS` (Success): $-0.20 \cdot \mathbf{w}_t$ (Reinforce current distribution).

2. **Regularized Gradient Step**:
   $$\mathbf{g}_{\text{total}} = \nabla_{\mathbf{w}} \mathcal{L} + \lambda (\mathbf{w}_t - \mathbf{w}_{\text{baseline}}) \quad (\lambda = 0.02)$$
   $$\Delta \mathbf{w} = \text{clip}(-\eta \cdot \mathbf{g}_{\text{total}}, -0.08, 0.08) \quad (\eta = 0.035 \cdot \text{scale})$$

3. **Euclidean Simplex Projection with Minimum Bound**:
   Solves:
   $$\min_{\mathbf{w}} \frac{1}{2} \|\mathbf{w} - (\mathbf{w}_t + \Delta \mathbf{w})\|_2^2 \quad \text{s.t.} \quad \sum_{i=1}^3 w_i = 1.0, \quad w_i \ge 0.05$$
   Guarantees that no modality is completely zeroed out or allowed to exceed 1.0.

---

### 3.5 Layer 5C: Macro-Adaptation State Machine
Implemented in [macro_adaptation.py](file:///d:/HCI/src/adaptation/macro_adaptation.py).

Governs long-term profile convergence across session lifecycles:

| Policy | Trigger Condition | System Action |
| :--- | :--- | :--- |
| **`MERGE`** | Stability index $\ge 0.85$, interactions $\ge 15$, stable duration $\ge 45\text{ s}$, state `STABLE`. | Blends session weights into permanent baseline profile: $\mathbf{w}_{\text{baseline}} \leftarrow (1 - \gamma)\mathbf{w}_{\text{baseline}} + \gamma \mathbf{w}_{\text{session}}$ ($\gamma = 0.50$). |
| **`FREEZE`** | Ambient illumination $< 15\text{ lux}$ or user face tracking lost. | Freezes all weight updates to prevent ingesting landmark noise. |
| **`DISCARD`** | EWMA gain $< -0.20$ and stability index $< 0.30$. | Reverts tentative weights to permanent baseline; discards session modifications. |
| **`RECALIBRATE`**| $\text{ECE} \ge 0.28$ across $\ge 15$ interactions. | Flags user profile for 9-point spatial recalibration wizard. |

---

## 4. Data Storage and Persistence Architecture

The system utilizes a structured, 4-tier storage hierarchy to manage persistent user states, supervisory logs, real-time sliding windows, and experimental datasets:

| Tier | Storage Location | Data Format | Managing Component | Purpose & Contents |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Master Profiles** | `data/profiles/{user_id}.json` | Strongly-Typed JSON | [ProfileManager](file:///d:/HCI/src/storage/profile_manager.py) | **Persistent User States**: Solved calibration matrices, modality fusion weights, action thresholds, gesture boundaries, dwell tempos, and version ID. |
| **Tier 2: Telemetry Logs** | `logs/feedback_events.jsonl` | Append-Only JSONL | [FeedbackTelemetryLogger](file:///d:/HCI/src/feedback/telemetry_logger.py) | **Supervisory Observations**: Real-time record of all implicit corrections, mouse takeovers, key undos, saccadic escapes, and dwell expirations. |
| **Tier 3: Runtime State** | In-Memory (RAM) | Ring Buffers & Deques | [AssessmentEngine](file:///d:/HCI/src/adaptation/assessment_engine.py), [Gatekeeper](file:///d:/HCI/src/adaptation/gatekeeper.py) | **Real-Time Sliding Windows**: Sliding interaction window ($N=30$), EWMA gain history, SPRT log-likelihood accumulator, and WebSocket queue. |
| **Tier 4: Study Datasets** | `data/benchmark_traces/`, `data/synthetic_outliers/` | CSV / JSON / NumPy | [StudyManager](file:///d:/HCI/src/evaluation/study_manager.py) | **Empirical Evaluation**: ISO 9241-9 trial results, throughput (bits/s), movement times, error rates, and Latin Square counterbalancing. |

---

### 4.1 Tier 1: Persistent User Profiles (`data/profiles/{user_id}.json`)
Implemented in [schemas.py](file:///d:/HCI/src/storage/schemas.py) and [profile_manager.py](file:///d:/HCI/src/storage/profile_manager.py).

Whenever the Macro-Adaptation state machine executes a `MERGE` or the user runs the spatial calibration wizard, profile parameters are persisted to disk.

#### Atomic Write Guarantee
To prevent corrupt profile files if power is interrupted or the process is killed mid-write, `ProfileManager` writes to a temporary file (`.json.tmp`) and performs an atomic filesystem swap (`os.replace`):
```python
target_path = self.get_profile_path(profile.user_id)
temp_path = target_path.with_suffix(".json.tmp")
with open(temp_path, "w", encoding="utf-8") as f:
    json.dump(profile.to_dict(), f, indent=2)
os.replace(temp_path, target_path)  # Atomic POSIX/Win32 swap
```

#### Persisted Fields in `ProfileSnapshot`:
- `user_id`: Unique identifier (e.g., `user_02`, `default_user`).
- `version_id`: Incremental version number (increments on each macro-merge or calibration).
- `timestamp_epoch`: Unix timestamp of the last persistent update.
- `modality_weights`: Action-specific fusion distribution ($[w_{\text{eye}}, w_{\text{head}}, w_{\text{hand}}]$) for 15 interaction verbs.
- `action_thresholds`: Required execution confidence per action (0.55 to 0.80).
- `gaze_calibration_matrix`: Solved decoupled eye-head affine ($2 \times 5$) and polynomial ($2 \times 9$) mapping matrices.
- `neutral_pose_mean` and `neutral_pose_cov_inv`: Mahalanobis rest-pose distribution parameters.
- `user_latency_tempo_tau`: User interaction tempo parameter.
- `gaze_target_dwell_ms`: Adjusted dwell window (default $120.0\text{ ms}$).
- `intentionality_dwell_ms`: Pre-click confirmation dwell (default $100.0\text{ ms}$).
- `gesture_thresholds`: Per-token activation boundaries for all 13 vocabulary primitives.
- `total_interactions_seen`: Total lifetime interactions processed.
- `total_updates_approved`: Total micro-SGD updates passed through the SPRT gate.
- `total_updates_rejected`: Total candidate updates rejected by the SPRT gate.
- `failure_counts_by_taxonomy`: Lifetime histogram of errors (`WRONG_TARGET`, `USER_OVERRIDE`, etc.).

---

### 4.2 Tier 2: Real-Time Supervisory Telemetry (`logs/feedback_events.jsonl`)
Implemented in [telemetry_logger.py](file:///d:/HCI/src/feedback/telemetry_logger.py).

Every supervisory observation detected by Layer 4 is written as an independent JSON line. This file acts as the immutable ground-truth audit trail for offline model validation and analytics.

#### Sample JSONL Telemetry Record:
```json
{
  "feedback_id": "fb_d8644d18",
  "action_id": "cmd_00001130",
  "timestamp": 1788092426.067,
  "latency_delta_t": 0.216,
  "feedback_type": "IMPLICIT_NEG",
  "confidence_cfb": 0.70,
  "failure_mode": "WRONG_TARGET",
  "severity": 2,
  "detector_source": "IMPLICIT_SACCADIC_ESCAPE",
  "raw_event_payload": {
    "gaze_escape_distance_px": 242.74,
    "delta_t": 0.216
  }
}
```

#### Thread Safety and File Rotation:
- Operations are protected by a reentrant mutex lock (`threading.RLock`).
- When `feedback_events.jsonl` reaches $25.0\text{ MB}$, the logger rotates the file to `feedback_events.jsonl.old` and begins a fresh log stream.

---

### 4.3 Tier 3: In-Memory Runtime Sliding Buffers
Implemented in [assessment_engine.py](file:///d:/HCI/src/adaptation/assessment_engine.py), [gatekeeper.py](file:///d:/HCI/src/adaptation/gatekeeper.py), and [server.py](file:///d:/HCI/src/testbench/server.py).

To satisfy the strict 60 FPS ($<16.6\text{ ms}$) processing deadline, statistical metrics are calculated in volatile memory without blocking on disk I/O:
- `AssessmentEngine._history`: Ring buffer (`collections.deque(maxlen=30)`) holding `(timestamp, is_success, confidence, weights_array)`.
- `Gatekeeper._sprt_score`: Floating-point scalar tracking the cumulative log-likelihood ratio $\Lambda_n$.
- `TestbenchServer._received_events`: In-memory list buffering verified interaction events received from the browser over WebSocket.

---

### 4.4 Tier 4: Evaluation Benchmark and User Study Datasets
Implemented in [study_manager.py](file:///d:/HCI/src/evaluation/study_manager.py).

Used during formalized empirical evaluations to log ISO 9241-9 pointing and selection trials:
- Records participant ID, experimental condition ($C_1$ through $C_4$), block index, target ID, Index of Difficulty ($ID$), Movement Time ($MT$), Throughput ($TP$ in bits/s), error count, and overshoot count.
- Stored as research data records for ANOVA and Wilcoxon statistical hypothesis testing.


---

## 5. How Repeated Testbench Runs Train the System

When a user executes the testbench:
```powershell
python scripts/run_testbench.py --user user_02
```

Each interaction cycle across Scenarios 01 through 06 provides structured reinforcement data:

```
Trial Progression:
┌────────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Bootstrapping (Trials 1 - 10)                                         │
│ • User establishes initial baseline.                                           │
│ • Natural tremor and gaze drift cause occasional hit misses.                   │
│ • SPRT accumulator gathers evidence on systematic offset.                      │
└────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Active Adaptation (Trials 11 - 30)                                    │
│ • SPRT threshold A is crossed; Micro-SGD updates approved.                     │
│ • Modality weights shift away from noisy channels toward stable channels.      │
│ • Dwell tempo adapts to user reaction speed.                                   │
│ • False activation rates drop significantly.                                   │
└────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Macro Convergence (Trials 31+)                                        │
│ • Weight stability index exceeds 0.85; System health reaches STABLE.           │
│ • Engine 5C executes MERGE into data/profiles/user_02.json (version_id++).     │
│ • Subsequent sessions load pre-adapted parameters immediately.                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Specific Error Reduction Mechanisms

1. **Gaze Jitter and Tremor Mitigation**:
   - *Problem*: High ocular tremor causes the cursor to leave target bounding boxes during pinch gestures.
   - *Adaptation*: `WRONG_TARGET` feedback reduces $w_{\text{eye}}$ while increasing $w_{\text{head}}$ and $w_{\text{hand}}$. Broad targeting relies on gaze; fine stabilization relies on head orientation and gesture locking.

2. **Elimination of the Midas Touch**:
   - *Problem*: Users looking at a target without intent to trigger trigger premature clicks.
   - *Adaptation*: The system raises `action_thresholds["PRIMARY_CLICK"]` and extends `intentionality_dwell_ms` until resting fixations produce zero false triggers.

3. **Individualized Pinch Kinematics**:
   - *Problem*: A user with reduced finger mobility produces index pinches peaking at confidence $0.67$, failing the default $0.70$ threshold.
   - *Adaptation*: Following repeated failed attempts followed by successful retries, the SPRT gate approves a downward adjustment of `gesture_thresholds["PINCH_INDEX"]` to $0.65$ without affecting other tokens.

4. **Fitts's Law Efficiency Optimization**:
   - Movement Time ($MT$) follows Fitts's Law:
     $$MT = a + b \log_2 \left(\frac{2D}{W}\right)$$
   - By personalizing the latency tempo $\tau$ and stabilizing the reticle, the index of difficulty coefficient $b$ decreases. Users achieve target acquisition in fewer corrective sub-movements.

---

## 6. Verification and Validation Reference

The closed-loop adaptation architecture is verified through automated test suites:

- **Integration Verification**: [test_closed_loop_adaptation.py](file:///d:/HCI/tests/integration/test_closed_loop_adaptation.py)
  - Simulates 10 successful interactions followed by 5 systematic `WRONG_TARGET` failure events.
  - Verifies invariant `INV-D5.6`: Simplex constraint preservation ($\sum w_i = 1.0$), minimum weight bounds ($w_i \ge 0.05$), SPRT gate approval, and expected weight shift away from the failing modality.
- **Latency Benchmark**: [test_adaptation_latency.py](file:///d:/HCI/tests/benchmarks/test_adaptation_latency.py)
  - Confirms end-to-end feedback evaluation, assessment calculation, and gradient projection complete within $< 1.5\text{ ms}$, maintaining full 60 FPS real-time headroom.
