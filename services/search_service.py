from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from database.db_manager import DatabaseManager
from database.models import Person
from utils.formatters import vietnamese_unaccent
from utils.logger import log_info, log_error

class SearchService:
    @staticmethod
    def search_persons_advanced(
        keyword: str = "",
        full_name: str = "",
        id_card: str = "",
        person_code: str = "",
        phone: str = "",
        hometown: str = "",
        area_id: int = 0,
        gender: str = "",
        residence_status: str = "",
        age_group: str = "",
        occupation: str = "",
        is_deleted: int = 0,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Person], int]:
        """
        Executes multi-condition advanced query optimized with SQLite Indexes.
        """
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            where_clauses = ["p.is_deleted = ?"]
            params = [is_deleted]

            # 1. Quick Keyword
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
                w_c = f"%{kw_clean}%"
                w_u = f"%{kw_unaccent}%"
                params.extend([w_c, w_c, w_u, w_c, w_c, w_c, w_c, w_c, w_c])

            # 2. Specific Field Filters
            if full_name and full_name.strip():
                fn_unaccent = vietnamese_unaccent(full_name.strip())
                where_clauses.append("(p.full_name LIKE ? OR p.normalized_name LIKE ?)")
                params.extend([f"%{full_name.strip()}%", f"%{fn_unaccent}%"])

            if id_card and id_card.strip():
                where_clauses.append("p.id_card_number LIKE ?")
                params.append(f"%{id_card.strip()}%")

            if person_code and person_code.strip():
                where_clauses.append("p.person_code LIKE ?")
                params.append(f"%{person_code.strip()}%")

            if phone and phone.strip():
                where_clauses.append("p.phone LIKE ?")
                params.append(f"%{phone.strip()}%")

            if hometown and hometown.strip():
                where_clauses.append("p.hometown LIKE ?")
                params.append(f"%{hometown.strip()}%")

            if occupation and occupation.strip():
                where_clauses.append("p.occupation LIKE ?")
                params.append(f"%{occupation.strip()}%")

            if area_id and area_id > 0:
                where_clauses.append("p.area_id = ?")
                params.append(area_id)

            if gender and gender not in ["", "Tất cả"]:
                where_clauses.append("p.gender = ?")
                params.append(gender)

            if residence_status and residence_status not in ["", "Tất cả"]:
                where_clauses.append("p.residence_status = ?")
                params.append(residence_status)

            # Age Demographic Filter
            if age_group and age_group != "Tất cả":
                curr_year = datetime.now().year
                if age_group == "0-18":
                    where_clauses.append(f"({curr_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 0 AND 18")
                elif age_group == "19-30":
                    where_clauses.append(f"({curr_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 19 AND 30")
                elif age_group == "31-45":
                    where_clauses.append(f"({curr_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 31 AND 45")
                elif age_group == "46-60":
                    where_clauses.append(f"({curr_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) BETWEEN 46 AND 60")
                elif age_group == "Trên 60":
                    where_clauses.append(f"({curr_year} - CAST(strftime('%Y', p.dob) AS INTEGER)) > 60")

            where_sql = " WHERE " + " AND ".join(where_clauses)

            # Count total matching query
            count_sql = f"SELECT COUNT(*) as total FROM persons p {where_sql}"
            cursor.execute(count_sql, params)
            total_records = cursor.fetchone()["total"]

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
                ORDER BY p.id DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(data_sql, params + [page_size, offset])
            rows = cursor.fetchall()
            persons = [Person.from_row(r) for r in rows]

            return persons, total_records
        except Exception as e:
            log_error(f"Error in advanced search: {e}", exc_info=True)
            return [], 0
        finally:
            conn.close()
