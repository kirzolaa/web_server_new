import threading
import time
import os
import sys
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from save_db import backup_database

class DbBackupService:
    def __init__(self, backup_interval=3600):  # Default backup every hour
        self.backup_interval = backup_interval
        self.running = False
        self.thread = None
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger('db_backup_service')
        handler = logging.FileHandler('db_backup_service.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def start(self):
        if self.running:
            self.logger.info("Service already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.thread.start()
        self.logger.info("Database backup service started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.logger.info("Database backup service stopped")

    def _backup_loop(self):
        while self.running:
            try:
                self.logger.info("Performing scheduled database backup")
                backup_database()
                self.logger.info("Backup completed successfully")
            except Exception as e:
                self.logger.error(f"Error during scheduled backup: {e}")

            # Sleep for the interval, but check periodically if we should stop
            for _ in range(self.backup_interval // 10):
                if not self.running:
                    break
                time.sleep(10)  # Check every 10 seconds if we should stop