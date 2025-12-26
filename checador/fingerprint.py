"""Fingerprint processing using NBIS (mindtct, bozorth3)."""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from checador.config import Config

logger = logging.getLogger(__name__)


class FingerprintMatcher:
    """NBIS-based fingerprint feature extraction and matching."""
    
    def __init__(self, config: Config):
        self.config = config
        self._verify_nbis_tools()
    
    def _verify_nbis_tools(self):
        """Verify NBIS tools are installed and accessible."""
        for tool in [self.config.fingerprint.nbis_mindtct, 
                     self.config.fingerprint.nbis_bozorth3]:
            tool_path = Path(tool)
            if not tool_path.exists():
                raise FileNotFoundError(
                    f"NBIS tool not found: {tool}\n"
                    f"Please install NBIS and update config.toml"
                )
    
    def extract_features(self, image_path: Path) -> Tuple[bool, Optional[Path], int]:
        """
        Extract minutiae features from fingerprint image using mindtct.
        
        Args:
            image_path: Path to grayscale PNG fingerprint image
        
        Returns:
            (success, xyt_path, quality_score)
        """
        try:
            # mindtct creates files in same directory as input
            # Output: image.xyt, image.min, image.qm, image.dm, image.hcm, image.lcm
            output_base = image_path.with_suffix('')
            xyt_path = output_base.with_suffix('.xyt')
            
            # Run mindtct
            cmd = [
                self.config.fingerprint.nbis_mindtct,
                str(image_path),
                str(output_base)
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                logger.error(f"mindtct failed: {result.stderr}")
                return False, None, 0
            
            # Check if XYT file was created
            if not xyt_path.exists():
                logger.error(f"XYT file not created: {xyt_path}")
                return False, None, 0
            
            # Calculate quality score from minutiae count
            quality = self._calculate_quality(xyt_path)
            
            logger.info(f"Features extracted: {xyt_path} (quality={quality})")
            return True, xyt_path, quality
            
        except subprocess.TimeoutExpired:
            logger.error("mindtct timed out")
            return False, None, 0
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return False, None, 0
    
    def _calculate_quality(self, xyt_path: Path) -> int:
        """
        Calculate quality score from XYT file.
        Quality = number of minutiae points found.
        """
        try:
            with open(xyt_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                return len(lines)
        except Exception as e:
            logger.warning(f"Error calculating quality: {e}")
            return 0
    
    def match_fingerprints(self, probe_xyt: Path, gallery_xyt: Path) -> Optional[int]:
        """
        Match two fingerprint templates using bozorth3.
        
        Args:
            probe_xyt: Probe (test) fingerprint XYT file
            gallery_xyt: Gallery (enrolled) fingerprint XYT file
        
        Returns:
            Match score (higher = better match), or None on error
        """
        try:
            cmd = [
                self.config.fingerprint.nbis_bozorth3,
                str(probe_xyt),
                str(gallery_xyt)
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                logger.error(f"bozorth3 failed: {result.stderr}")
                return None
            
            # Parse score from output (single integer)
            try:
                score = int(result.stdout.strip())
                logger.debug(f"Match score: {score}")
                return score
            except ValueError:
                logger.error(f"Invalid bozorth3 output: {result.stdout}")
                return None
            
        except subprocess.TimeoutExpired:
            logger.error("bozorth3 timed out")
            return None
        except Exception as e:
            logger.error(f"Error matching fingerprints: {e}")
            return None
    
    def identify(self, probe_xyt: Path, gallery_templates: List[Tuple[int, Path]]) -> Optional[Tuple[int, int]]:
        """
        Identify fingerprint against gallery of templates.
        
        Args:
            probe_xyt: Probe fingerprint XYT file
            gallery_templates: List of (template_id, xyt_path) tuples
        
        Returns:
            (template_id, score) of best match above threshold, or None
        """
        best_score = 0
        best_template_id = None
        
        for template_id, gallery_xyt in gallery_templates:
            score = self.match_fingerprints(probe_xyt, gallery_xyt)
            if score is None:
                continue
            
            if score > best_score:
                best_score = score
                best_template_id = template_id
        
        # Check threshold
        if best_score >= self.config.fingerprint.match_threshold:
            logger.info(f"Match found: template_id={best_template_id}, score={best_score}")
            return best_template_id, best_score
        
        logger.info(f"No match found (best score={best_score}, threshold={self.config.fingerprint.match_threshold})")
        return None