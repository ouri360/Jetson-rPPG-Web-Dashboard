"""
Webcam Streaming module with OpenCV library (Multithreaded).
---------------------------------------
Provides a robust, zero-blocking interface for capturing video frames.
Automatically spawns a background I/O thread for live webcams to prevent 
the USB controller from bottlenecking the Jetson Orin CPU.
"""

import cv2
import logging
import threading
from typing import Tuple, Optional, Union
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebcamStream:
    """
    Interface for capturing video frames from a live webcam OR a video file.
    """
    def __init__(self, source: Union[int, str] = 0):
        self.source = source
        self.is_live = isinstance(self.source, int)
        
        # 1. Initialize Backend
        if self.is_live:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
        else:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG) 
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Critical Error: Could not open video source: {self.source}.")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0 or np.isnan(self.fps):
            self.fps = 30.0 
            logging.warning("Could not read FPS from source. Defaulting to 30.0 FPS.")

        logging.info(f"Video source initialized successfully. Operating at {self.fps} FPS.")

       # 2. Hardware Locking (Version Adaptative Universelle)
        if self.is_live:
            logging.info("Live camera detected. Running adaptive hardware calibration...")
            
            # On laisse OpenCV négocier la meilleure configuration native
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            # ÉTAPE A : Préchauffage (Warm-up) en mode automatique
            # On laisse l'ISP de la caméra s'adapter à la luminosité et aux couleurs de la pièce
            # (V4L2: 3 = Mode Auto, 1 = Mode Manuel)
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3) 
            self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)      
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)    
            self.cap.set(cv2.CAP_PROP_FOCUS, 0)

            import time
            # On lit quelques frames pour laisser les filtres matériels se stabiliser
            for _ in range(15):
                self.cap.read()
                time.sleep(0.01)

            # ÉTAPE B : Lecture des paramètres optimaux calculés par le matériel
            current_exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            current_gain = self.cap.get(cv2.CAP_PROP_GAIN)
            
            # Log de contrôle pour l'ingénieur
            fourcc_int = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            fourcc_str = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]) if fourcc_int > 0 else "RAW"
            logging.info(f"Format Vidéo Actif : {fourcc_str} | Exposure Auto-détectée : {current_exposure} | Gain Auto-détecté : {current_gain}")

            # ÉTAPE C : Verrouillage Intelligent (Pour la stabilité mathématique du rPPG)
            if current_exposure > 0:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # Passage en Manuel
                self.cap.set(cv2.CAP_PROP_EXPOSURE, current_exposure) # On fige l'exposition trouvée
            
            # Gestion de la balance des blancs anti-teinte verte
            # Si c'est une webcam intégrée (qui renvoie souvent un gain à 0 ou un format compressé MJPG),
            # désactiver l'auto-WB détruit ses couleurs. On la laisse donc en Auto-WB pour la sécurité.
            if "YUYV" in fourcc_str and current_gain > 0:
                self.cap.set(cv2.CAP_PROP_AUTO_WB, 0) # Verrouillage manuel pour caméra générique
                self.cap.set(cv2.CAP_PROP_GAIN, current_gain)
            else:
                self.cap.set(cv2.CAP_PROP_AUTO_WB, 1) # Maintien de l'auto-WB pour PC portable
                logging.warning("Webcam type PC portable détectée. Maintien de l'Auto-WB pour éviter la teinte verte.")

        # 3. Multithreading Setup
        self.ret = False
        self.frame = None
        self.stopped = False

        self.new_frame_event = threading.Event()

        if self.is_live:
            # Read the very first frame to establish the connection before threading
            self.ret, self.frame = self.cap.read()
            
            # Spawn the background I/O Thread
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            logging.info("Background I/O Thread started.")
        else:
            logging.info("Video file detected. Using standard sequential reading for testing.")

    def _update(self) -> None:
        """
        Runs continuously in the background thread (ONLY for live webcams).
        Constantly pulls the USB bus and stores the absolute latest frame in RAM.
        """
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                break
            
            self.ret = ret
            self.frame = frame
            self.new_frame_event.set()

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Returns the instantly available frame without waiting for hardware."""
        if self.is_live:
            # Return the cached frame instantly
            if self.stopped and self.frame is None:
                return False, None
            
            self.new_frame_event.wait()
            self.new_frame_event.clear()

            # Return a copy to prevent the background thread from overwriting it while main.py draws the UI
            return self.ret, self.frame.copy() if self.frame is not None else None
        else:
            # Standard blocking read for exact frame-by-frame video processing
            return self.cap.read()

    def release(self) -> None:
        """Shuts down the thread and the camera."""
        self.stopped = True
        
        if self.is_live and hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
            
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            
        logging.info("Video source released safely.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

if __name__ == "__main__":
    try:
        with WebcamStream(source=0) as cam:
            while True:
                success, current_frame = cam.read_frame()
                if not success:
                    break
                
                cv2.imshow("Multithreaded Webcam Test (Press 'q' to quit)", current_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except Exception as e:
        logging.error(f"Application crashed: {e}")
    finally:
        cv2.destroyAllWindows()