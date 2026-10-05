from typing import List, Optional, Tuple, Dict
from database.db_manager import DatabaseManager
from database.models import Area
from utils.logger import log_info, log_error

class AreaController:
    def __init__(self):
        self.db = DatabaseManager()

    def get_all_areas(self) -> List[Area]:
        """Returns list of all areas with person and household counts."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT 
                    a.id, a.code, a.name, a.description, a.created_at, a.updated_at,
                    (SELECT COUNT(*) FROM persons p WHERE p.area_id = a.id AND p.is_deleted = 0) as person_count,
                    (SELECT COUNT(*) FROM households h WHERE h.area_id = a.id AND h.status = 'ACTIVE') as household_count
                FROM areas a
                ORDER BY a.name ASC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            return [Area.from_row(row) for row in rows]
        except Exception as e:
            log_error(f"Error fetching areas: {e}")
            return []
        finally:
            conn.close()

    def get_area_by_id(self, area_id: int) -> Optional[Area]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT 
                    a.id, a.code, a.name, a.description, a.created_at, a.updated_at,
                    (SELECT COUNT(*) FROM persons p WHERE p.area_id = a.id AND p.is_deleted = 0) as person_count,
                    (SELECT COUNT(*) FROM households h WHERE h.area_id = a.id AND h.status = 'ACTIVE') as household_count
                FROM areas a
                WHERE a.id = ?
            """
            cursor.execute(query, (area_id,))
            row = cursor.fetchone()
            return Area.from_row(row) if row else None
        finally:
            conn.close()

    def add_area(self, code: str, name: str, description: str = "") -> Tuple[bool, str, Optional[int]]:
        """Creates a new area."""
        code = code.strip().upper()
        name = name.strip()
        if not code or not name:
            return False, "Mã khu vực và Tên khu vực không được để trống.", None

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM areas WHERE code = ? OR name = ?", (code, name))
            if cursor.fetchone():
                return False, f"Mã khu vực '{code}' hoặc Tên khu vực '{name}' đã tồn tại.", None

            cursor.execute(
                "INSERT INTO areas (code, name, description) VALUES (?, ?, ?)",
                (code, name, description)
            )
            conn.commit()
            area_id = cursor.lastrowid
            log_info(f"Created area ID {area_id}: {name}")
            return True, "Thêm khu vực thành công!", area_id
        except Exception as e:
            conn.rollback()
            log_error(f"Error adding area: {e}")
            return False, f"Lỗi khi thêm khu vực: {e}", None
        finally:
            conn.close()

    def update_area(self, area_id: int, code: str, name: str, description: str = "") -> Tuple[bool, str]:
        """Updates area info."""
        code = code.strip().upper()
        name = name.strip()
        if not code or not name:
            return False, "Mã khu vực và Tên khu vực không được để trống."

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM areas WHERE (code = ? OR name = ?) AND id != ?", (code, name, area_id))
            if cursor.fetchone():
                return False, f"Mã khu vực '{code}' hoặc Tên khu vực '{name}' bị trùng với khu vực khác."

            cursor.execute(
                "UPDATE areas SET code = ?, name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (code, name, description, area_id)
            )
            conn.commit()
            return True, "Cập nhật thông tin khu vực thành công!"
        except Exception as e:
            conn.rollback()
            log_error(f"Error updating area {area_id}: {e}")
            return False, f"Lỗi khi cập nhật khu vực: {e}"
        finally:
            conn.close()

    def delete_area(self, area_id: int) -> Tuple[bool, str]:
        """Deletes an area if no active persons or households are assigned to it."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM persons WHERE area_id = ? AND is_deleted = 0", (area_id,))
            if cursor.fetchone()["count"] > 0:
                return False, "Không thể xóa khu vực này vì đang có nhân khẩu sinh sống. Vui lòng chuyển nhân khẩu sang khu vực khác trước."

            cursor.execute("SELECT COUNT(*) as count FROM households WHERE area_id = ?", (area_id,))
            if cursor.fetchone()["count"] > 0:
                return False, "Không thể xóa khu vực này vì đang có hộ gia đình đăng ký. Vui lòng chuyển hộ gia đình sang khu vực khác trước."

            cursor.execute("DELETE FROM areas WHERE id = ?", (area_id,))
            conn.commit()
            return True, "Xóa khu vực thành công!"
        except Exception as e:
            conn.rollback()
            log_error(f"Error deleting area {area_id}: {e}")
            return False, f"Lỗi khi xóa khu vực: {e}"
        finally:
            conn.close()

    def transfer_population(self, source_area_id: int, target_area_id: int) -> Tuple[bool, str, int]:
        """Transfers all persons from source area to target area."""
        if source_area_id == target_area_id:
            return False, "Khu vực nguồn và khu vực đích không được giống nhau.", 0

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE persons SET area_id = ?, updated_at = CURRENT_TIMESTAMP WHERE area_id = ?", (target_area_id, source_area_id))
            transferred_persons = cursor.rowcount
            cursor.execute("UPDATE households SET area_id = ?, updated_at = CURRENT_TIMESTAMP WHERE area_id = ?", (target_area_id, source_area_id))
            transferred_hh = cursor.rowcount
            conn.commit()
            return True, f"Đã chuyển thành công {transferred_persons} nhân khẩu và {transferred_hh} hộ gia đình sang khu vực mới.", transferred_persons
        except Exception as e:
            conn.rollback()
            log_error(f"Error transferring population: {e}")
            return False, f"Lỗi khi chuyển địa bàn: {e}", 0
        finally:
            conn.close()
