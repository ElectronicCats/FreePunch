"""Camera calibration endpoint."""

import logging

from fastapi import APIRouter, Response
from pydantic import BaseModel

from checador.camera import CameraManager
from checador.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


class ROIRequest(BaseModel):
    x: int
    y: int
    width: int
    height: int


@router.get("/stream")
async def video_stream():
    """Stream camera feed for calibration."""
    config = get_config()
    camera = CameraManager(config)
    
    jpeg = camera.get_frame_jpeg()
    if jpeg is None:
        return Response(status_code=503, content="Camera not available")
    
    return Response(content=jpeg, media_type="image/jpeg")


@router.post("/roi")
async def set_roi(roi: ROIRequest):
    """Set camera ROI."""
    config = get_config()
    
    # Update config
    config.camera.roi_x = roi.x
    config.camera.roi_y = roi.y
    config.camera.roi_width = roi.width
    config.camera.roi_height = roi.height
    
    # Save to file
    config.save()
    
    logger.info(f"ROI updated: ({roi.x}, {roi.y}, {roi.width}, {roi.height})")
    
    return {"success": True, "message": "ROI saved"}