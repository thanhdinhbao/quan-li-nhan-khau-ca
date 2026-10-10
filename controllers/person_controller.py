from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Person
from utils.formatters import vietnamese_unaccent, parse_date_to_iso
from utils.validators import validate_full_name, validate_id_card, validate_dob, validate_phone
from utils.logger import log_info, log_error

class PersonController:
    def __init__(self):
        self.db = DatabaseManager()

    @staticmethod
    def generate_person_code() -> str:
        """Generates next unique NK code (e.g. NK000009)."""
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(id) as max_id FROM persons")
            row = cursor.fetchone()
            max_id = row["max_id"] if row and row["max_id"] else 0

            cursor.execute("SELECT MAX(CAST(SUBSTR(person_code, 3) AS INTEGER)) as max_code FROM persons WHERE person_code LIKE 'NK%'")
            row_code = cursor.fetchone()
            max_code = row_code["max_code"] if row_code and row_code["max_code"] else 0

            next_num = max(max_id, max_code) + 1
            while True:
                candidate = f"NK{next_num:06d}"
                cursor.execute("SELECT 1 FROM persons WHERE person_code = ?", (candidate,))
                if not cursor.fetchone():
                    return candidate
                next_num += 1
        finally:
            conn.close()

    def check_duplicate_id_card(self, id_card_number: str, exclude_person_id: Optional[int] = None) -> bool:
        """Checks if non-empty CCCD already exists in active records."""
        if not id_card_number or not id_card_number.strip():
            return False
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            if exclude_person_id:
                cursor.execute(
                    "SELECT id FROM persons WHERE id_card_number = ? AND id != ? AND is_deleted = 0",
                    (id_card_number.strip(), exclude_person_id)
                )
            else:
                cursor.execute(
                    "SELECT id FROM persons WHERE id_card_number = ? AND is_deleted = 0",
                    (id_card_number.strip(),)
                )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def get_persons_paged(
        self,
        keyword: str = "",
        area_id: Optional[int] = None,
        gender: Optional[str] = None,
        age_group: Optional[str] = None,
        residence_status: Optional[str] = None,
        is_deleted: int = 0,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "id",
        sort_order: str = "DESC"
    ) -> Tuple[List[Person], int]:
        """
        Retrieves paginated persons matching filters.
        Supports unaccented Vietnamese search across name, code, CCCD, phone, address.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            where_clauses = ["p.is_deleted = ?"]
            params = [is_deleted]

            if area_id and area_id > 0:
                where_clauses.append("p.area_id = ?")
                params.append(area_id)

            if gender and gender != "Tất cả" and not gender.startswith("Tất cả"):
                where_clauses.append("p.gender = ?")
                params.append(gender)

            if residence_status and residence_status != "Tất cả" and not residence_status.startswith("Tất cả"):
                where_clauses.append("p.residence_status = ?")
                params.append(residence_status)

            if keyword and keyword.strip():
                kw_clean = keyword.strip()
                kw_unaccent = vietnamese_unaccent(kw_clean)
                where_clauses.append("""
                    (
                        p.person_code LIKE ? OR
                        p.full_name LIKE ? OR
                        p.normalized_name LIKE ? OR
                        p.id_card_number LIKE ? OR
                        p.phone LIKE ? OR
                        p.hometown LIKE ? OR
                        p.permanent_address LIKE ? OR
                        p.occupation LIKE ? OR
                        p.workplace LIKE ?
                    )
                """)
                wildcard = f"%{kw_clean}%"
                wildcard_unaccent = f"%{kw_unaccent}%"
                params.extend([wildcard, wildcard, wildcard_unaccent, wildcard, wildcard, wildcard, wildcard, wildcard, wildcard])

            # Age group filtering in SQL based on strftime year
            if age_group and age_group != "Tất cả":
                current_year = datetime.now().year
                if age_group == "0-18":
                    where_clauses.append(f"({current_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 0 AND 18")
                elif age_group == "19-30":
                    where_clauses.append(f"({current_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 19 AND 30")
                elif age_group == "31-45":
                    where_clauses.append(f"({current_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 31 AND 45")
                elif age_group == "46-60":
                    where_clauses.append(f"({current_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 46 AND 60")
                elif age_group == "Trên 60":
                    where_clauses.append(f"({current_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) > 60")

            where_sql = " WHERE " + " AND ".join(where_clauses)

            # Count total query
            count_sql = f"SELECT COUNT(*) as total FROM persons p {where_sql}"
            cursor.execute(count_sql, params)
            total_records = cursor.fetchone()["total"]

            # Sanitization of sort fields
            allowed_sorts = {
                "id": "p.id",
                "person_code": "p.person_code",
                "full_name": "p.full_name",
                "dob": "p.dob",
                "gender": "p.gender",
                "id_card_number": "p.id_card_number",
                "area_name": "a.name"
            }
            sort_column = allowed_sorts.get(sort_by, "p.id")
            order_dir = "ASC" if sort_order.upper() == "ASC" else "DESC"

            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT 
                    p.*,
                    a.name as area_name,
                    h.household_code
                FROM persons p
                LEFT JOIN areas a ON p.area_id = a.id
                LEFT JOIN households h ON p.household_id = h.id
                {where_sql}
                ORDER BY {sort_column} {order_dir}
                LIMIT ? OFFSET ?
            """
            data_params = params + [page_size, offset]
            cursor.execute(data_sql, data_params)
            rows = cursor.fetchall()
            persons = [Person.from_row(r) for r in rows]

            return persons, total_records
        except Exception as e:
            log_error(f"Error fetching paged persons: {e}", exc_info=True)
            return [], 0
        finally:
            conn.close()

    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT p.*, a.name as area_name, h.household_code
                FROM persons p
                LEFT JOIN areas a ON p.area_id = a.id
                LEFT JOIN households h ON p.household_id = h.id
                WHERE p.id = ?
            """
            cursor.execute(sql, (person_id,))
            row = cursor.fetchone()
            return Person.from_row(row) if row else None
        finally:
            conn.close()

    def add_person(self, p: Person, user_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:
        """Validates and creates a new Person record."""
        # Validation checks
        valid, msg = validate_full_name(p.full_name)
        if not valid:
            return False, msg, None

        if p.dob:
            valid, msg = validate_dob(p.dob)
            if not valid:
                return False, msg, None

        if p.id_card_number and p.id_card_number.strip():
            valid, msg = validate_id_card(p.id_card_number)
            if not valid:
                return False, msg, None
            if self.check_duplicate_id_card(p.id_card_number):
                return False, f"Số CCCD '{p.id_card_number}' đã tồn tại trong cơ sở dữ liệu.", None

        if p.phone and p.phone.strip():
            valid, msg = validate_phone(p.phone)
            if not valid:
                return False, msg, None

        if not p.person_code or not p.person_code.strip():
            p.person_code = PersonController.generate_person_code()

        p.normalized_name = vietnamese_unaccent(p.full_name)
        p.dob = parse_date_to_iso(p.dob)
        p.id_card_date = parse_date_to_iso(p.id_card_date)
        p.permanent_reg_date = parse_date_to_iso(p.permanent_reg_date)
        p.temporary_reg_date = parse_date_to_iso(p.temporary_reg_date)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO persons (
                    person_code, full_name, normalized_name, dob, gender, id_card_number, id_card_date, id_card_place,
                    hometown, ethnicity, nationality, religion, occupation, workplace, phone, email, marital_status,
                    permanent_address, temporary_address, current_address, area_id, house_number, street_village,
                    permanent_reg_date, temporary_reg_date, residence_status, father_name, father_id_card,
                    mother_name, mother_id_card, spouse_name, spouse_id_card, relationship_with_head, household_id,
                    avatar_path, notes, created_by, updated_by
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                p.person_code, p.full_name.strip(), p.normalized_name, p.dob, p.gender,
                p.id_card_number.strip() if p.id_card_number else "", p.id_card_date, p.id_card_place,
                p.hometown, p.ethnicity or "Kinh", p.nationality or "Việt Nam", p.religion or "Không",
                p.occupation, p.workplace, p.phone, p.email, p.marital_status,
                p.permanent_address, p.temporary_address, p.current_address, p.area_id, p.house_number, p.street_village,
                p.permanent_reg_date, p.temporary_reg_date, p.residence_status, p.father_name, p.father_id_card,
                p.mother_name, p.mother_id_card, p.spouse_name, p.spouse_id_card, p.relationship_with_head, p.household_id,
                p.avatar_path, p.notes, user_id, user_id
            ))
            conn.commit()
            pid = cursor.lastrowid
            log_info(f"Added person ID {pid} - Code: {p.person_code}")
            return True, "Thêm mới nhân khẩu thành công!", pid
        except Exception as e:
            conn.rollback()
            log_error(f"Error adding person: {e}", exc_info=True)
            return False, f"Lỗi khi thêm nhân khẩu: {e}", None
        finally:
            conn.close()

    def update_person(self, p: Person, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """Updates an existing Person record."""
        if not p.id:
            return False, "ID nhân khẩu không hợp lệ."

        valid, msg = validate_full_name(p.full_name)
        if not valid:
            return False, msg

        if p.dob:
            valid, msg = validate_dob(p.dob)
            if not valid:
                return False, msg

        if p.id_card_number and p.id_card_number.strip():
            valid, msg = validate_id_card(p.id_card_number)
            if not valid:
                return False, msg
            if self.check_duplicate_id_card(p.id_card_number, exclude_person_id=p.id):
                return False, f"Số CCCD '{p.id_card_number}' bị trùng với một nhân khẩu khác."

        if p.phone and p.phone.strip():
            valid, msg = validate_phone(p.phone)
            if not valid:
                return False, msg

        p.normalized_name = vietnamese_unaccent(p.full_name)
        p.dob = parse_date_to_iso(p.dob)
        p.id_card_date = parse_date_to_iso(p.id_card_date)
        p.permanent_reg_date = parse_date_to_iso(p.permanent_reg_date)
        p.temporary_reg_date = parse_date_to_iso(p.temporary_reg_date)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE persons SET
                    full_name = ?, normalized_name = ?, dob = ?, gender = ?, id_card_number = ?, id_card_date = ?, id_card_place = ?,
                    hometown = ?, ethnicity = ?, nationality = ?, religion = ?, occupation = ?, workplace = ?, phone = ?, email = ?, marital_status = ?,
                    permanent_address = ?, temporary_address = ?, current_address = ?, area_id = ?, house_number = ?, street_village = ?,
                    permanent_reg_date = ?, temporary_reg_date = ?, residence_status = ?, father_name = ?, father_id_card = ?,
                    mother_name = ?, mother_id_card = ?, spouse_name = ?, spouse_id_card = ?, relationship_with_head = ?, household_id = ?,
                    avatar_path = ?, notes = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (
                p.full_name.strip(), p.normalized_name, p.dob, p.gender,
                p.id_card_number.strip() if p.id_card_number else "", p.id_card_date, p.id_card_place,
                p.hometown, p.ethnicity, p.nationality, p.religion, p.occupation, p.workplace, p.phone, p.email, p.marital_status,
                p.permanent_address, p.temporary_address, p.current_address, p.area_id, p.house_number, p.street_village,
                p.permanent_reg_date, p.temporary_reg_date, p.residence_status, p.father_name, p.father_id_card,
                p.mother_name, p.mother_id_card, p.spouse_name, p.spouse_id_card, p.relationship_with_head, p.household_id,
                p.avatar_path, p.notes, user_id, p.id
            ))
            conn.commit()
            log_info(f"Updated person ID {p.id}")
            return True, "Cập nhật thông tin nhân khẩu thành công!"
        except Exception as e:
            conn.rollback()
            log_error(f"Error updating person {p.id}: {e}", exc_info=True)
            return False, f"Lỗi khi cập nhật nhân khẩu: {e}"
        finally:
            conn.close()

    def soft_delete_person(self, person_id: int, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """Soft-deletes person (sets is_deleted = 1)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE persons SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP, updated_by = ? WHERE id = ?",
                (user_id, person_id)
            )
            conn.commit()
            return True, "Đã chuyển hồ sơ nhân khẩu vào thùng rác."
        except Exception as e:
            conn.rollback()
            return False, f"Lỗi khi xóa nhân khẩu: {e}"
        finally:
            conn.close()

    def restore_person(self, person_id: int, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """Restores soft-deleted person."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE persons SET is_deleted = 0, deleted_at = NULL, updated_by = ? WHERE id = ?",
                (user_id, person_id)
            )
            conn.commit()
            return True, "Đã khôi phục hồ sơ nhân khẩu thành công!"
        except Exception as e:
            conn.rollback()
            return False, f"Lỗi khi khôi phục nhân khẩu: {e}"
        finally:
            conn.close()

    def get_dashboard_statistics(self, area_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculates dashboard metrics and statistics."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            area_filter = "AND p.area_id = ?" if area_id and area_id > 0 else ""
            params = [area_id] if area_id and area_id > 0 else []

            # Total persons
            cursor.execute(f"SELECT COUNT(*) as cnt FROM persons p WHERE p.is_deleted = 0 {area_filter}", params)
            total_persons = cursor.fetchone()["cnt"]

            # Males & Females
            cursor.execute(f"SELECT COUNT(*) as cnt FROM persons p WHERE p.is_deleted = 0 AND p.gender = 'Nam' {area_filter}", params)
            total_males = cursor.fetchone()["cnt"]

            cursor.execute(f"SELECT COUNT(*) as cnt FROM persons p WHERE p.is_deleted = 0 AND p.gender = 'Nữ' {area_filter}", params)
            total_females = cursor.fetchone()["cnt"]

            # Households count
            hh_area_filter = "WHERE area_id = ?" if area_id and area_id > 0 else ""
            hh_params = [area_id] if area_id and area_id > 0 else []
            cursor.execute(f"SELECT COUNT(*) as cnt FROM households {hh_area_filter}", hh_params)
            total_households = cursor.fetchone()["cnt"]

            # Areas count
            cursor.execute("SELECT COUNT(*) as cnt FROM areas")
            total_areas = cursor.fetchone()["cnt"]

            # Records needing verification (e.g. missing CCCD or incomplete profile)
            cursor.execute(f"""
                SELECT COUNT(*) as cnt FROM persons p 
                WHERE p.is_deleted = 0 AND (p.id_card_number IS NULL OR p.id_card_number = '' OR p.phone IS NULL OR p.phone = '')
                {area_filter}
            """, params)
            records_needing_check = cursor.fetchone()["cnt"]

            # Incomplete profile (missing hometown or occupation)
            cursor.execute(f"""
                SELECT COUNT(*) as cnt FROM persons p 
                WHERE p.is_deleted = 0 AND (p.hometown IS NULL OR p.hometown = '' OR p.occupation IS NULL OR p.occupation = '')
                {area_filter}
            """, params)
            incomplete_records = cursor.fetchone()["cnt"]

            # Population by area
            cursor.execute("""
                SELECT a.name as area_name, COUNT(p.id) as count
                FROM areas a
                LEFT JOIN persons p ON a.id = p.area_id AND p.is_deleted = 0
                GROUP BY a.id, a.name
                ORDER BY count DESC
            """)
            pop_by_area = {row["area_name"]: row["count"] for row in cursor.fetchall()}

            # Households by area
            cursor.execute("""
                SELECT a.name as area_name, COUNT(h.id) as count
                FROM areas a
                LEFT JOIN households h ON a.id = h.area_id AND h.status = 'ACTIVE'
                GROUP BY a.id, a.name
                ORDER BY count DESC
            """)
            hh_by_area = {row["area_name"]: row["count"] for row in cursor.fetchall()}

            # Age demographics
            current_year = datetime.now().year
            cursor.execute(f"""
                SELECT 
                    SUM(CASE WHEN ({current_year} - CAST(strftime('%Y', dob) AS INTEGER)) BETWEEN 0 AND 18 THEN 1 ELSE 0 END) as g_0_18,
                    SUM(CASE WHEN ({current_year} - CAST(strftime('%Y', dob) AS INTEGER)) BETWEEN 19 AND 30 THEN 1 ELSE 0 END) as g_19_30,
                    SUM(CASE WHEN ({current_year} - CAST(strftime('%Y', dob) AS INTEGER)) BETWEEN 31 AND 45 THEN 1 ELSE 0 END) as g_31_45,
                    SUM(CASE WHEN ({current_year} - CAST(strftime('%Y', dob) AS INTEGER)) BETWEEN 46 AND 60 THEN 1 ELSE 0 END) as g_46_60,
                    SUM(CASE WHEN ({current_year} - CAST(strftime('%Y', dob) AS INTEGER)) > 60 THEN 1 ELSE 0 END) as g_above_60
                FROM persons p
                WHERE p.is_deleted = 0 {area_filter}
            """, params)
            age_row = cursor.fetchone()
            age_demo = {
                "0-18": age_row["g_0_18"] or 0,
                "19-30": age_row["g_19_30"] or 0,
                "31-45": age_row["g_31_45"] or 0,
                "46-60": age_row["g_46_60"] or 0,
                "Trên 60": age_row["g_above_60"] or 0
            }

            return {
                "total_persons": total_persons,
                "total_males": total_males,
                "total_females": total_females,
                "total_households": total_households,
                "total_areas": total_areas,
                "records_needing_check": records_needing_check,
                "incomplete_records": incomplete_records,
                "pop_by_area": pop_by_area,
                "hh_by_area": hh_by_area,
                "age_demographics": age_demo
            }
        except Exception as e:
            log_error(f"Error calculating dashboard stats: {e}", exc_info=True)
            return {}
        finally:
            conn.close()
