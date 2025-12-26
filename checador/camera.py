"""Camera capture and ROI management for UVC fingerprint reader."""

import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from checador.config import Config

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages V4L2 camera capture and ROI processing."""
    
    def __init__(self, config: Config):
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self._is_open = False
    
    def open(self) -> bool:
        """Open camera device."""
        try:
            device = self.config.camera.device
            logger.info(f"Opening camera: {device}")
            
            self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera: {device}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.camera.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.camera.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.camera.fps)
            
            self._is_open = True
            logger.info("Camera opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def close(self):
        """Close camera device."""
        if self.cap:
            self.cap.release()
            self._is_open = False
            logger.info("Camera closed")
    
    def is_open(self) -> bool:
        """Check if camera is open."""
        return self._is_open and self.cap is not None and self.cap.isOpened()
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from camera."""
        if not self.is_open():
            if not self.open():
                return None
        
        try:
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("Failed to read frame")
                self._is_open = False
                return None
            
            return frame
            
        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            self._is_open = False
            return None
    
    def capture_roi(self) -> Optional[np.ndarray]:
        """Capture frame and extract ROI."""
        frame = self.capture_frame()
        if frame is None:
            return None
        
        # Extract ROI
        x = self.config.camera.roi_x
        y = self.config.camera.roi_y
        w = self.config.camera.roi_width
        h = self.config.camera.roi_height
        
        # Validate ROI bounds
        height, width = frame.shape[:2]
        if x < 0 or y < 0 or x + w > width or y + h > height:
            logger.warning(f"Invalid ROI bounds: ({x},{y},{w},{h}) for frame {width}x{height}")
            return frame  # Return full frame as fallback
        
        roi = frame[y:y+h, x:x+w]
        return roi
    
    def capture_fingerprint(self, output_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Capture fingerprint image and save as grayscale PNG.
        
        Returns:
            (success, error_message)
        """
        try:
            roi = self.capture_roi()
            if roi is None:
                return False, "Failed to capture frame from camera"
            
            # Convert to grayscale
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
            
            # Save as PNG
            output_path.parent.mkdir(parents=True, exist_ok=True)
            success = cv2.imwrite(str(output_path), gray)
            
            if not success:
                return False, "Failed to save image"
            
            logger.info(f"Fingerprint image saved: {output_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error capturing fingerprint: {e}")
            return False, str(e)
    
    def get_frame_jpeg(self) -> Optional[bytes]:
        """Get current frame as JPEG bytes for streaming."""
        frame = self.capture_frame()
        if frame is None:
            return None
        
        try:
            # Draw ROI rectangle
            x = self.config.camera.roi_x
            y = self.config.camera.roi_y
            w = self.config.camera.roi_width
            h = self.config.camera.roi_height
            
            display_frame = frame.copy()
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Encode as JPEG
            ret, jpeg = cv2.imencode('.jpg', display_frame)
            if not ret:
                return None
            
            return jpeg.tobytes()
            
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return None
    
    def test_camera(self) -> dict:
        """Test camera and return diagnostics."""
        result = {
            "device": self.config.camera.device,
            "accessible": False,
            "opened": False,
            "frame_captured": False,
            "roi_valid": False,
            "resolution": None,
            "error": None,
        }
        
        try:
            # Check device exists
            device_path = Path(self.config.camera.device)
            if not device_path.exists():
                result["error"] = f"Device not found: {self.config.camera.device}"
                return result
            
            result["accessible"] = True
            
            # Try to open
            if not self.open():
                result["error"] = "Failed to open camera"
                return result
            
            result["opened"] = True
            
            # Try to capture
            frame = self.capture_frame()
            if frame is None:
                result["error"] = "Failed to capture frame"
                return result
            
            result["frame_captured"] = True
            result["resolution"] = f"{frame.shape[1]}x{frame.shape[0]}"
            
            # Check ROI
            x, y = self.config.camera.roi_x, self.config.camera.roi_y
            w, h = self.config.camera.roi_width, self.config.camera.roi_height
            
            if x >= 0 and y >= 0 and x + w <= frame.shape[1] and y + h <= frame.shape[0]:
                result["roi_valid"] = True
            else:
                result["error"] = f"ROI out of bounds: ({x},{y},{w},{h}) for {result['resolution']}"
            
        except Exception as e:
            result["error"] = str(e)
        
        finally:
            self.close()
        
        return result