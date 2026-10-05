from typing import List, Optional, Tuple, Dict, Any
from database.db_manager import DatabaseManager
from database.models import Household, Person
from utils.logger import log_info, log_error

class HouseholdController:
    def __init__(self):
        self.db = DatabaseManager()

    def generate_household_code(self) -> str:
        """Generates next household code HK000005..."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(id) as max_id FROM households")
            row = cursor.fetchone()
            max_id = row["max_id"] if row and row["max_id"] else 0
            return f"HK{max_id + 1:06d}"
        finally:
            conn.close()

    def get_households_paged(
        self,
        keyword: str = "",
        area_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Household], int]:
        """Retrieves paginated households matching search query."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            where_clauses = ["1=1"]
            params = []

            if area_id and area_id > 0:
                where_clauses.append("h.area_id = ?")
                params.append(area_id)

            if keyword and keyword.strip():
                kw = f"%{keyword.strip()}%"
                where_clauses.append("""
                    (
                        h.household_code LIKE ? OR
                        h.household_number LIKE ? OR
                        h.full_address LIKE ? OR
                        p.full_name LIKE ? OR
                        p.id_card_number LIKE ?
                    )
                """)
                params.extend([kw, kw, kw, kw, kw])

            where_sql = " WHERE " + " AND ".join(where_clauses)

            count_sql = f"""
                SELECT COUNT(*) as total
                FROM households h
                LEFT JOIN persons p ON h.head_person_id = p.id
                {where_sql}
            """
            cursor.execute(count_sql, params)
            total_records = cursor.fetchone()["total"]

            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT 
                    h.*,
                    a.name as area_name,
                    p.full_name as head_full_name,
                    (SELECT COUNT(*) FROM household_members hm WHERE hm.household_id = h.id AND hm.status = 'ACTIVE') as member_count
                FROM households h
                LEFT JOIN areas a ON h.area_id = a.id
                LEFT JOIN persons p ON h.head_person_id = p.id
                {where_sql}
                ORDER BY h.id DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(data_sql, params + [page_size, offset])
            rows = cursor.fetchall()
            households = [Household.from_row(r) for r in rows]
            return households, total_records
        except Exception as e:
            log_error(f"Error fetching households: {e}", exc_info=True)
            return [], 0
        finally:
            conn.close()

    def get_household_details(self, household_id: int) -> Optional[Household]:
        """Retrieves household object with all its members."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT 
                    h.*,
                    a.name as area_name,
                    p.full_name as head_full_name,
                    (SELECT COUNT(*) FROM household_members hm WHERE hm.household_id = h.id AND hm.status = 'ACTIVE') as member_count
                FROM households h
                LEFT JOIN areas a ON h.area_id = a.id
                LEFT JOIN persons p ON h.head_person_id = p.id
                WHERE h.id = ?
            """
            cursor.execute(sql, (household_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            hh = Household.from_row(row)

            # Get members
            members_sql = """
                SELECT p.*, a.name as area_name, hm.relationship
                FROM household_members hm
                JOIN persons p ON hm.person_id = p.id
                LEFT JOIN areas a ON p.area_id = a.id
                WHERE hm.household_id = ? AND hm.status = 'ACTIVE' AND p.is_deleted = 0
                ORDER BY 
                    CASE WHEN hm.relationship = 'Chủ hộ' THEN 0 ELSE 1 END,
                    p.dob ASC
            """
            cursor.execute(members_sql, (household_id,))
            member_rows = cursor.fetchall()
            hh.members = [Person.from_row(mr) for mr in member_rows]
            return hh
        finally:
            conn.close()

    def add_household(self, household_code: str, household_number: str, area_id: int, address_street: str, full_address: str, head_person_id: Optional[int] = None, notes: str = "") -> Tuple[bool, str, Optional[int]]:
        """Creates a new household."""
        if not household_code or not household_code.strip():
            household_code = self.generate_household_code()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM households WHERE household_code = ?", (household_code.strip(),))
            if cursor.fetchone():
                return False, f"Mã hộ gia đình '{household_code}' đã tồn tại.", None

            cursor.execute("""
                INSERT INTO households (household_code, household_number, area_id, head_person_id, address_street, full_address, created_date, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, DATE('now'), 'ACTIVE', ?)
            """, (household_code.strip(), household_number.strip(), area_id, head_person_id, address_street, full_address, notes))
            conn.commit()
            hh_id = cursor.lastrowid

            if head_person_id:
                # Add head to household_members
                cursor.execute("""
                    INSERT OR REPLACE INTO household_members (household_id, person_id, relationship, joined_date, status)
                    VALUES (?, ?, 'Chủ hộ', DATE('now'), 'ACTIVE')
                """, (hh_id, head_person_id))
                # Update person table household_id & relationship
                cursor.execute("""
                    UPDATE persons SET household_id = ?, relationship_with_head = 'Chủ hộ', updated_at = CURRENT_TIMESTAMP WHERE id = ?
                """, (hh_id, head_person_id))
                conn.commit()

            return True, "Thêm mới hộ gia đình thành công!", hh_id
        except Exception as e:
            conn.rollback()
            log_error(f"Error adding household: {e}", exc_info=True)
            return False, f"Lỗi khi thêm hộ gia đình: {e}", None
        finally:
            conn.close()

    def add_member_to_household(self, household_id: int, person_id: int, relationship: str) -> Tuple[bool, str]:
        """Adds or updates a person's membership in a household."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            # If relationship is 'Chủ hộ', update head_person_id of household
            if relationship == "Chủ hộ":
                cursor.execute("UPDATE households SET head_person_id = ? WHERE id = ?", (person_id, household_id))
            
            cursor.execute("""
                INSERT OR REPLACE INTO household_members (household_id, person_id, relationship, joined_date, status)
                VALUES (?, ?, ?, DATE('now'), 'ACTIVE')
            """, (household_id, person_id, relationship))

            cursor.execute("""
                UPDATE persons SET household_id = ?, relationship_with_head = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (household_id, relationship, person_id))

            conn.commit()
            return True, "Thêm thành viên vào hộ gia đình thành công!"
        except Exception as e:
            conn.rollback()
            log_error(f"Error adding member to household: {e}")
            return False, f"Lỗi khi thêm thành viên: {e}"
        finally:
            conn.close()

    def remove_member_from_household(self, household_id: int, person_id: int) -> Tuple[bool, str]:
        """Removes a person from household."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM household_members WHERE household_id = ? AND person_id = ?", (household_id, person_id))
            cursor.execute("UPDATE persons SET household_id = NULL, relationship_with_head = NULL WHERE id = ?", (person_id,))
            
            # Check if person was head
            cursor.execute("SELECT head_person_id FROM households WHERE id = ?", (household_id,))
            row = cursor.fetchone()
            if row and row["head_person_id"] == person_id:
                cursor.execute("UPDATE households SET head_person_id = NULL WHERE id = ?", (household_id,))

            conn.commit()
            return True, "Đã tách thành viên khỏi hộ gia đình."
        except Exception as e:
            conn.rollback()
            return False, f"Lỗi khi xóa thành viên khỏi hộ: {e}"
        finally:
            conn.close()
