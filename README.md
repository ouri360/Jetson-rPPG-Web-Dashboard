Voici le fichier `README.md` complet, regroupé en **un seul bloc de code unique** sans aucune interruption de texte. Tu peux le copier et le coller directement dans ton fichier sur GitHub :

```markdown
# High-Performance rPPG Web Dashboard on NVIDIA Jetson Orin Nano

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![NVIDIA Jetson](https://img.shields.io/badge/NVIDIA-Jetson%20Orin%20Nano-green.svg)](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/)
[![JetPack](https://img.shields.io/badge/JetPack-6.2.2-76B900.svg)](https://grid.nvidia.com/)
[![Framework](https://img.shields.io/badge/Flask-Web%20Framework-lightgrey.svg)](https://flask.palletsprojects.com/)

An edge-optimized, real-time **Remote Photoplethysmography (rPPG)** system designed for contactless heart rate estimation and ECG-like wave extraction. This project implements a hierarchical **Plane-Orthogonal-to-Skin (POS)** core algorithm with dynamic, regional **inverse-variance fusion**, engineered specifically to maximize compute efficiency on resource-constrained embedded platforms.

---

## 🚀 Key Engineering Features

- **Embedded Edge Optimization:** Tailored specifically for the **NVIDIA Jetson Orin Nano (JetPack 6.2.2)**. Features zero-blocking multithreaded V4L2 camera capture pipelines and frame decimation strategies to bypass standard USB and scheduling bottlenecks.
- **Hierarchical Regional POS Fusion:** Divides the face into 5 dynamic micro-ROIs (3x Forehead, Left/Right Cheeks). It extracts independent orthogonal skin-plane reflections, completely isolating biological signals from non-uniform ambient or specular illumination artifacts.
- **Statistical Noise-Immunity:** Uses an automatic inverse-variance weighting mechanism based on real-time standard deviation metrics. Moving patches (e.g., mouth movement, localized shadows) are statistically penalized in under 2ms using highly optimized NumPy vectorization.
- **Dual-Interface Flexibility:** Designed with an isolated core processor layer enabling both an advanced, asynchronous Flask Web Dashboard (with lightweight Chart.js graphics) and a low-latency native OpenCV GUI.

---

## 🛠️ System Architecture & Pipeline

The software bypasses heavy Deep Learning models to prioritize deterministic, real-time CPU memory-mapped efficiency:

1. **Hardware Ingestion (`webcam.py`):** Spawns a background I/O thread querying the camera subsystem. Incorporates an automatic hardware warmup phase to capture and lock V4L2 auto-exposure, gain, and white balance settings, guaranteeing absolute optical stability.
2. **Dynamic ROI Tracking (`detector.py`):** Uses an optimized MediaPipe FaceMesh mesh-generation loop to track facial geometries. Implements convex hull mask-caching to eliminate CPU redundancy across frames.
3. **Signal Processing Core (`processor.py`):** - Normalizes temporal sub-window overlaps via a strict Overlap-Add (OLA) correction array.
   - Computes localized Alphas ($\alpha = \sigma(S_1)/\sigma(S_2)$) independently per sub-region.
   - Filters the synchronized stream using an adaptive, physiological dual-bandpass filter (Butterworth 3rd order, tracking centered around a ±0.35 Hz target heart rate window).
   - Extracts exact spectral densities via Fast Fourier Transform (FFT).

---

## 📋 Prerequisites & Requirements

### Hardware Target
- **Platform:** NVIDIA Jetson Orin Nano (4GB or 8GB Developer Kit)
- **OS / Software Stack:** Ubuntu 22.04 LTS with **JetPack 6.2.2**
- **Sensor:** Standard USB Linux-supported (UVC/V4L2) Webcam (Optimized for 640x480 @ 30 FPS)

### Python Dependencies Explained
The architecture relies entirely on a lightweight, scientific, non-CUDA python stack to keep a minimal memory footprint on the Jetson:

* `numpy`: Handles ultra-fast multi-dimensional matrix operations, algorithmic orthogonal projections, and mathematical array fusions.
* `opencv-python`: Manages V4L2 frame ingestion, color-space conversions (BGR to RGB), and matrix drawing operations (Inferno colormaps).
* `mediapipe`: Drives the face mesh landmark regression engine efficiently on the CPU ARM cores.
* `scipy`: Supplies advanced digital signal processing utilities (`scipy.signal.butter`, `detrend`, `sosfiltfilt`) for physiological noise isolation.
* `flask`: Serves as the micro-web server, implementing non-blocking streaming generators to push serialized JSON telemetry data and MJPEG buffers asynchronously.

---

## ⚙️ Installation & Setup

1. **Clone the Repository Cleanly:**
   ```bash
   git clone [https://github.com/ouri360/Jetson-rPPG-Web-Dashboard.git](https://github.com/ouri360/Jetson-rPPG-Web-Dashboard.git)
   cd Jetson-rPPG-Web-Dashboard

```

2. **Establish a Clean Virtual Environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate

```


3. **Install Dependencies:**
```bash
pip install --upgrade pip
pip install numpy opencv-python mediapipe scipy flask

```



---

## 🎮 Execution: How to Run

The pipeline features a decoupled interface layout depending on your deployment scenario:

### 🌐 Option A: Asynchronous Web Dashboard (Recommended)

Launches the full Flask micro-service. This deploys a modern web dashboard streaming live webcam feeds alongside hardware-accelerated, real-time Chart.js renderings of the filtered ECG-like waveform and raw FFT Power Spectral Densities (displaying both Hz and corresponding BPM metrics linearly).

```bash
python3 app.py

```

*Once initialized, open any desktop or network browser and navigate to:* `http://localhost:5000`

* **Idle Mode:** MediaPipe actively tracks landmarks with zero color overlay to conserve processor bandwidth. Only the clean white tracking contours are drawn.
* **Active Mode (Click "START rPPG"):** Spawns a dedicated mathematical background thread, drawing localized real-time SNR weights directly on the face using a solid mathematical *Inferno* colormap while simultaneously updating the biometric charts and clearing historical buffers cleanly upon stop.

### 💻 Option B: Native Local UI (Testing & Debugging)

Launches a low-overhead window directly on the Jetson display server using OpenCV's native HighGUI system. This option is ideal for benchmarking processing frame rates and validating pure pipeline latencies without browser network constraints.

```bash
python3 main.py

```

*Press `Q` inside the OpenCV window to terminate the thread safely.*

---

## 🔬 Scientific & Algorithmic Highlights

For technical recruiters and R&D evaluators, here is why this implementation achieves state-of-the-art deterministic robustness:

* **True Regional Alpha Isolation:** Unlike naive implementations that apply a global alpha parameter across the whole face, this architecture applies the plane rotation $\mathbf{h} = S_1 + \alpha S_2$ *locally* inside each sub-region. This ensures that a localized artifact (e.g., shadows on a single cheek) does not corrupt the clean physiological signatures captured on the forehead.
* **Overlap-Add (OLA) Normalization:** Because temporal windows overlap by over 91% (`step=4` frames on a 1.6s buffer), a custom density accumulation vector tracks exactly how many sub-windows have contributed to each time-slice, neutralizing amplitude distortions before feeding the array to the SciPy filtering chain.

```text
[Frame Buffer] ---> [OLA Density Array] ---> [Detrending] ---> [Adaptive Filter] ---> [FFT Core]

```

---

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).

```

```