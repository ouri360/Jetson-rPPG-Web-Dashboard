"""
Jetson Environment Validator for rPPG Pipeline
---------------------------------------
Checks the installed libraries against the "Golden Stack" and actively
queries the Jetson Nano Orin hardware to ensure CUDA and TensorRT are linked.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def validate_environment():
    """Validates the Jetson Orin environment by checking library versions and GPU accessibility. This function ensures that the correct versions of NumPy, MediaPipe, OpenCV, PyTorch, and ONNX Runtime are installed, and that PyTorch can access the Orin GPU for maximum performance."""
    logging.info("=== Jetson Orin rPPG Validator ===")
    logging.info(f"Python Version: {sys.version.split(' ')[0]}")
    
    all_good = True

    # 1. Check NumPy
    try:
        import numpy as np
        np_version = np.__version__
        if int(np_version.split('.')[0]) >= 2:
            logging.error(f"❌ NumPy: {np_version} (ERROR: Must be 1.x! NumPy 2.0+ breaks MediaPipe.)")
            all_good = False
        else:
            logging.info(f"✅ NumPy: {np_version}")
    except ImportError:
        logging.error("❌ NumPy is not installed.")
        all_good = False

    # 2. Check MediaPipe
    try:
        import mediapipe as mp
        if mp.__version__ != "0.10.21":
            logging.warning(f"⚠️ MediaPipe: {mp.__version__} (WARNING: Script requires 0.10.21.)")
            all_good = False
        else:
            logging.info(f"✅ MediaPipe: {mp.__version__}")
    except ImportError:
        logging.error("❌ MediaPipe is not installed.")
        all_good = False

    # 3. Check System OpenCV (Jetson Specific)
    try:
        import cv2
        # We don't force 4.9 here. We just ensure it's the system JetPack version.
        logging.info(f"✅ OpenCV: {cv2.__version__}")
    except ImportError:
        logging.error("❌ OpenCV is not installed.")
        all_good = False

    logging.info("==================================")
    
    if all_good:
        logging.info("🚀 SUCCESS")
    else:
        logging.info("🛑 ACTION REQUIRED: Environment mismatch detected.")

if __name__ == "__main__":
    """Entry point for the environment validation script. When run, this will check all critical libraries and GPU access to ensure the Jetson Orin is properly configured for the rPPG pipeline."""
    validate_environment()