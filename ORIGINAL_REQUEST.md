# Original User Request

## Initial Request — 2026-07-13T22:27:46+08:00

Refactor and optimise the AhabAssistantLimbusCompany game automation engine to improve input simulation, anti-detection (evasion), vision recognition efficiency, state control, and resolve critical shop bugs.

Working directory: C:\Users\AscAed\worktrees\AhabAssistantLimbusCompany\refactor-limbus-automation-engine
Integrity mode: development

## Requirements

### R1. Humanised Low-Level Input Simulation
- Refactor the input handlers to simulate human-like cursor movements using Bézier curves.
- In Win32 background mode, generate and post simulated `WM_MOUSEMOVE` coordinates along the Bézier path prior to mouse down.
- Apply randomized delay distributions (Gaussian or Poisson) for press-and-release durations and step intervals.
- Create an interface in the input handlers allowing integration of driver-level/hardware simulation inputs.

### R2. Vision Recognition Optimisation
- Define and enforce Region of Interest (ROI) scan boundaries for specific elements (shop grids, road nodes) to avoid full-screen scans.
- Implement a location matching cache: successful matches should cache coordinate positions and search within a micro-ROI on subsequent frames before falling back to full searches.
- Replace slow ORB feature matching with multi-scale template matching or pixel color checks for routine navigation.

### R3. Lightweight State Control Flow
- Transition control loops to a lightweight page-based state checking mechanism.
- Replace rigid sleep delays with active dynamic polling (`wait_until_appear` with timeouts).
- Support automated process restart and state recovery when network connection issues or game crashes are detected.

### R4. Shop Fusion and EGO Gift Observation Fixes
- Fix shop fusion ("合成：四级优先"): locate commodities dynamically using grid template matching/OCR, identify levels (I-IV), and correctly synthesise exactly three non-system items.
- Fix EGO gift observation: use Level indicator tags (Level I/II/III) as dynamic coordinate anchors instead of hardcoded cumulative offsets, verifying positions after scrolling.

## Acceptance Criteria

### Input Simulation
- [ ] Mouse clicks and drags do not happen at fixed coordinates or instant jumps; they follow curved trajectories and exhibit randomized intervals.
- [ ] Keyboard typing uses variable press-release delays.

### Vision and Flow
- [ ] Match operations for static buttons complete in under 10ms when cached.
- [ ] Dynamic wait methods poll UI states at short, randomized periods instead of blocking with fixed sleep calls.

### Shop & EGO Logic
- [ ] Shop fusion correctly synthesises level IV items without clicking wrong items or locking up.
- [ ] EGO gift selection accurately identifies target gifts across various scales/resolutions using level anchors and falls back to OCR if templates fail.
