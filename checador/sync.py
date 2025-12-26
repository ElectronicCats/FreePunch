"""Background sync worker for syncing punches to server."""

import asyncio
import logging
from datetime import datetime
from typing import List

import httpx

from checador.config import Config
from checador.database import Database, Punch, User

logger = logging.getLogger(__name__)


class SyncWorker:
    """Background worker to sync punches to server."""
    
    def __init__(self, config: Config, database: Database):
        self.config = config
        self.db = database
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    def start(self):
        """Start background sync worker."""
        if not self.config.server.enabled:
            logger.info("Server sync disabled")
            return
        
        if self.running:
            logger.warning("Sync worker already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._sync_loop())
        logger.info("Sync worker started")
    
    def stop(self):
        """Stop background sync worker."""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Sync worker stopped")
    
    async def _sync_loop(self):
        """Main sync loop."""
        retry_count = 0
        
        while self.running:
            try:
                # Try to sync
                success = await self.sync_now()
                
                if success:
                    retry_count = 0
                    # Normal interval
                    await asyncio.sleep(self.config.server.sync_interval_seconds)
                else:
                    # Exponential backoff
                    retry_count = min(retry_count + 1, self.config.server.retry_max_attempts)
                    backoff = self.config.server.retry_backoff_base ** retry_count
                    logger.warning(f"Sync failed, retry in {backoff}s (attempt {retry_count})")
                    await asyncio.sleep(backoff)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                await asyncio.sleep(60)
    
    async def sync_now(self) -> bool:
        """
        Sync unsynced punches to server now.
        
        Returns:
            True if successful or no punches to sync
        """
        if not self.config.server.enabled:
            logger.info("Sync disabled")
            return True
        
        if not self.config.server.url:
            logger.warning("Server URL not configured")
            return True
        
        try:
            # Get unsynced punches
            punches = await self.db.get_unsynced_punches(limit=100)
            
            if not punches:
                logger.debug("No punches to sync")
                return True
            
            logger.info(f"Syncing {len(punches)} punches to server")
            
            # Prepare payload
            punch_data = []
            for punch in punches:
                user = await self.db.get_user(punch.user_id)
                if not user:
                    continue
                
                punch_data.append({
                    "user_id": user.id,
                    "employee_code": user.employee_code,
                    "timestamp_utc": punch.timestamp_utc.isoformat(),
                    "timestamp_local": punch.timestamp_local.isoformat(),
                    "punch_type": punch.punch_type,
                    "match_score": punch.match_score,
                    "device_id": punch.device_id,
                })
            
            payload = {
                "device_id": self.config.app.device_id,
                "punches": punch_data,
            }
            
            # Send to server
            headers = {
                "Authorization": f"Bearer {self.config.server.api_key}",
                "Content-Type": "application/json",
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.config.server.url}/punches",
                    json=payload,
                    headers=headers,
                )
            
            if response.status_code == 200:
                # Mark as synced
                punch_ids = [p.id for p in punches]
                await self.db.mark_punches_synced(punch_ids)
                logger.info(f"Successfully synced {len(punches)} punches")
                return True
            else:
                error = f"Server returned {response.status_code}: {response.text}"
                logger.error(f"Sync failed: {error}")
                
                # Mark error on punches
                for punch in punches:
                    await self.db.mark_punch_sync_error(punch.id, error)
                
                return False
                
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return False
    
    async def get_status(self) -> dict:
        """Get sync status."""
        unsynced = await self.db.get_unsynced_punches(limit=1000)
        
        return {
            "enabled": self.config.server.enabled,
            "running": self.running,
            "server_url": self.config.server.url if self.config.server.enabled else None,
            "unsynced_count": len(unsynced),
        }