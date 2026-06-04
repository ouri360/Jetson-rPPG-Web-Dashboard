# High-Performance rPPG Web Dashboard on NVIDIA Jetson Orin Nano

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![NVIDIA Jetson](https://img.shields.io/badge/NVIDIA-Jetson%20Orin%20Nano-green.svg)](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/)
[![JetPack](https://img.shields.io/badge/JetPack-6.2.2-76B900.svg)](https://developer.nvidia.com/embedded/jetpack)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An edge-optimized, real-time **Remote Photoplethysmography (rPPG)** system for contactless heart rate estimation and ECG-like waveform extraction. This project implements a hierarchical **Plane-Orthogonal-to-Skin (POS)** algorithm with dynamic, regional **inverse-variance fusion**, engineered to maximize compute efficiency on resource-constrained embedded platforms.

---

## Table of Contents

1. [Key Engineering Features](#-key-engineering-features)
2. [System Architecture & Pipeline](#️-system-architecture--pipeline)
3. [Prerequisites & Requirements](#-prerequisites--requirements)
4. [Installation & Setup](#️-installation--setup)
5. [Running the Project](#-running-the-project)
6. [Scientific & Algorithmic Highlights](#-scientific--algorithmic-highlights)
7. [License](#-license)

---

## 🚀 Key Engineering Features

- **Embedded Edge Optimization** — Tailored for the NVIDIA Jetson Orin Nano (JetPack 6.2.2). Features zero-blocking multithreaded V4L2 camera capture pipelines and frame decimation strategies to bypass standard USB and scheduling bottlenecks.

- **Hierarchical Regional POS Fusion** — Divides the face into 5 dynamic micro-ROIs (3× Forehead, Left/Right Cheeks). Extracts independent orthogonal skin-plane reflections, isolating biological signals from non-uniform ambient or specular illumination artifacts.

- **Statistical Noise Immunity** — Automatic inverse-variance weighting based on real-time standard deviation metrics. Moving patches (e.g., mouth movement, localized shadows) are statistically penalized in under 2 ms using optimized NumPy vectorization.

- **Dual-Interface Flexibility** — Decoupled core processor layer enabling both an asynchronous Flask Web Dashboard (with Chart.js graphics) and a low-latency native OpenCV GUI.

---

## 🛠️ System Architecture & Pipeline

The software bypasses heavy deep learning models to prioritize deterministic, real-time CPU memory-mapped efficiency:

| Module | File | Role |
|---|---|---|
| Hardware Ingestion | `webcam.py` | Background I/O thread with V4L2 auto-exposure locking |
| ROI Tracking | `detector.py` | MediaPipe FaceMesh with convex hull mask-caching |
| Signal Processing | `processor.py` | OLA normalization, POS fusion, adaptive bandpass, FFT |
| Web Interface | `app.py` | Flask micro-server with MJPEG + JSON streaming |
| Native GUI | `main.py` | Low-overhead OpenCV HighGUI for benchmarking |

### Processing Chain

```
[V4L2 Frame] ──► [MediaPipe FaceMesh] ──► [5× Micro-ROI Extraction]
                                                       │
                                          [Per-Region POS α Computation]
                                                       │
                                          [Inverse-Variance Fusion]
                                                       │
                                            [OLA Density Array] ──► [Detrending] ──► [Adaptive Bandpass] ──► [FFT Core]
                                                                                                                │
                                                                                        [BPM Estimate + ECG-like Waveform]
```

### Pipeline Steps

1. **Hardware Ingestion (`webcam.py`)** — Spawns a background I/O thread querying the camera subsystem. Includes an automatic hardware warmup phase that captures and locks V4L2 auto-exposure, gain, and white balance settings, guaranteeing optical stability.

2. **Dynamic ROI Tracking (`detector.py`)** — Uses an optimized MediaPipe FaceMesh loop to track facial geometries. Implements convex hull mask-caching to eliminate CPU redundancy across frames.

3. **Signal Processing Core (`processor.py`)**
   - Normalizes temporal sub-window overlaps via a strict **Overlap-Add (OLA)** correction array.
   - Computes localized Alphas $\left(\alpha = \frac{\sigma(S_1)}{\sigma(S_2)}\right)$ independently per sub-region.
   - Filters the synchronized stream with an adaptive dual-bandpass filter (Butterworth 3rd order, centered ±0.35 Hz around the tracked heart rate window).
   - Extracts spectral densities via **Fast Fourier Transform (FFT)**.

---

## 📋 Prerequisites & Requirements

### Hardware Target

| Component | Specification |
|---|---|
| Platform | NVIDIA Jetson Orin Nano (4 GB or 8 GB Developer Kit) |
| Operating System | Ubuntu 22.04 LTS + JetPack 6.2.2 |
| Camera | UVC/V4L2 USB Webcam — optimized for 640×480 @ 30 FPS |

### Python Dependencies

The stack is intentionally lightweight and non-CUDA to maintain a minimal memory footprint on the Jetson:

| Package | Purpose |
|---|---|
| `numpy` | Multi-dimensional matrix operations, orthogonal projections, array fusions |
| `opencv-python` | V4L2 frame ingestion, color-space conversion (BGR→RGB), Inferno colormap rendering |
| `mediapipe` | CPU-based face mesh landmark regression on ARM cores |
| `scipy` | Digital signal processing — `butter`, `detrend`, `sosfiltfilt` |
| `flask` | Non-blocking micro-server streaming JSON telemetry and MJPEG buffers |

---

## ⚙️ Installation & Setup

**1. Clone the repository:**

```bash
git clone https://github.com/ouri360/Jetson-rPPG-Web-Dashboard.git
cd Jetson-rPPG-Web-Dashboard
```

**2. Create and activate a virtual environment:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies:**

```bash
pip install --upgrade pip
pip install numpy opencv-python mediapipe scipy flask
```

---

## 🎮 Running the Project

### Option A — Web Dashboard *(Recommended)*

Launches the full Flask micro-service with a live webcam feed, real-time Chart.js ECG-like waveform, and FFT Power Spectral Density visualization (in both Hz and BPM).

```bash
python3 app.py
```

Open a browser and navigate to: **`http://localhost:5000`**

| Mode | Behavior |
|---|---|
| **Idle** | MediaPipe tracks landmarks with white contour overlays only — no color rendering, minimal CPU load |
| **Active** (click *START rPPG*) | Spawns a background math thread; draws real-time SNR weights using an Inferno colormap; streams biometric charts live |

### Option B — Native OpenCV GUI *(Debugging & Benchmarking)*

Launches a lightweight HighGUI window directly on the Jetson display. Ideal for validating pipeline latency without browser overhead.

```bash
python3 main.py
```

> Press `Q` inside the OpenCV window to terminate safely.

---

## 🔬 Scientific & Algorithmic Highlights

### True Regional Alpha Isolation

Unlike naive implementations that apply a single global alpha across the entire face, this architecture applies the plane rotation:

$$\mathbf{h} = S_1 + \alpha \cdot S_2$$

*locally* within each sub-region. A localized artifact (e.g., a shadow on one cheek) therefore cannot corrupt the clean physiological signal captured on the forehead.

### Overlap-Add (OLA) Normalization

Temporal windows overlap by over 91% (`step = 4` frames on a 1.6 s buffer). A custom density accumulation vector tracks exactly how many sub-windows have contributed to each time slice, neutralizing amplitude distortions before the signal enters the SciPy filtering chain:

```
[Frame Buffer] ──► [OLA Density Array] ──► [Detrending] ──► [Adaptive Bandpass] ──► [FFT Core]
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).