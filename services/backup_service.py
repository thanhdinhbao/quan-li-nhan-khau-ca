import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from config import DB_PATH, BACKUP_DIR
from utils.logger import log_info, log_error

class BackupService:
    @staticmethod
    def create_backup(target_dir: Path = None) -> Tuple[bool, str, Optional[str]]:
        """Creates a timestamped backup copy of SQLite database."""
        dest_dir = target_dir or BACKUP_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_population_{timestamp}.db"
        backup_path = dest_dir / backup_name

        try:
            # Check SQLite integrity before backing up
            if not BackupService.verify_db_integrity(DB_PATH):
                return False, "Cơ sở dữ liệu gốc bị lỗi tính toàn vẹn. Không thể sao lưu.", None

            shutil.copy2(DB_PATH, backup_path)
            log_info(f"Database backup created: {backup_path}")
            return True, f"Sao lưu cơ sở dữ liệu thành công!\nFile: {backup_name}", str(backup_path)
        except Exception as e:
            log_error(f"Error creating DB backup: {e}", exc_info=True)
            return False, f"Lỗi khi sao lưu DB: {e}", None

    @staticmethod
    def restore_backup(backup_file_path: str) -> Tuple[bool, str]:
        """Restores database from backup file safely."""
        bp = Path(backup_file_path)
        if not bp.exists():
            return False, "File sao lưu không tồn tại."

        # Verify integrity of backup file
        if not BackupService.verify_db_integrity(bp):
            return False, "File sao lưu bị hư hỏng hoặc không phải là database SQLite hợp lệ."

        try:
            # Create emergency pre-restore snapshot
            emergency_name = f"pre_restore_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(DB_PATH, BACKUP_DIR / emergency_name)

            # Copy backup to active DB_PATH
            shutil.copy2(bp, DB_PATH)
            log_info(f"Database restored from: {backup_file_path}")
            return True, "Khôi phục cơ sở dữ liệu thành công!"
        except Exception as e:
            log_error(f"Error restoring DB: {e}", exc_info=True)
            return False, f"Lỗi khi phục hồi DB: {e}"

    @staticmethod
    def verify_db_integrity(db_file: Path) -> bool:
        """Executes PRAGMA integrity_check on SQLite file."""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            conn.close()
            return res and res[0] == "ok"
        except Exception:
            return False

    @staticmethod
    def list_backups() -> List[Dict[str, Any]]:
        """Returns list of existing backup files."""
        if not BACKUP_DIR.exists():
            return []
        
        backups = []
        for f in BACKUP_DIR.glob("*.db"):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "filepath": str(f),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
            })
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
