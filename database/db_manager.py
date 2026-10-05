import sqlite3
import hashlib
import os
import secrets
from pathlib import Path
from datetime import datetime, date
from config import DB_PATH, APP_NAME, APP_SUBTITLE
from utils.constants import (
    ROLE_ADMIN, ROLE_OFFICER, ROLE_VIEWER, ROLE_NAMES, DEFAULT_ROLE_PERMISSIONS
)
from utils.formatters import vietnamese_unaccent
from utils.logger import log_info, log_error

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hashes password using PBKDF2 with SHA256 and a random salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex(), salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies typed password against stored hash."""
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, stored_hash)

class DatabaseManager:
    _instance = None

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = db_path or DB_PATH
            cls._instance._init_db()
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Returns a new connection with row_factory set to sqlite3.Row."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        return conn

    def _init_db(self):
        """Initializes database schema and populates seed data if empty."""
        log_info(f"Initializing database at {self.db_path}")
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        conn = self.get_connection()
        try:
            try:
                conn.execute("PRAGMA journal_mode = WAL;")
            except sqlite3.OperationalError:
                pass

            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            if not cursor.fetchone():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                self._seed_initial_data(conn)
        except Exception as e:
            conn.rollback()
            log_error(f"Error initializing database: {e}", exc_info=True)
            raise e
        finally:
            conn.close()

    def _seed_initial_data(self, conn: sqlite3.Connection):
        cursor = conn.cursor()

        # 1. Seed Roles
        for code, name in ROLE_NAMES.items():
            cursor.execute("""
                INSERT OR IGNORE INTO roles (role_code, role_name, description)
                VALUES (?, ?, ?)
            """, (code, name, f"Vai trò {name}"))

        # Fetch role IDs
        cursor.execute("SELECT id, role_code FROM roles")
        role_map = {row["role_code"]: row["id"] for row in cursor.fetchall()}

        # 2. Seed Permissions
        for role_code, perms in DEFAULT_ROLE_PERMISSIONS.items():
            role_id = role_map.get(role_code)
            if role_id:
                for perm in perms:
                    cursor.execute("""
                        INSERT OR IGNORE INTO permissions (role_id, permission_code)
                        VALUES (?, ?)
                    """, (role_id, perm))

        # 3. Seed Default Users
        # Admin User: admin / admin123
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            pass_hash, salt = hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, role_id, position, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('admin', pass_hash, salt, 'Quản trị viên Hệ thống', role_map[ROLE_ADMIN], 'Chỉ huy Công an xã', 'admin@conganxa.gov.vn', '0912345678'))

        # Officer User: officer / officer123
        cursor.execute("SELECT id FROM users WHERE username = 'officer'")
        if not cursor.fetchone():
            pass_hash, salt = hash_password("officer123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, role_id, position, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('officer', pass_hash, salt, 'Nguyễn Văn An', role_map[ROLE_OFFICER], 'Cán bộ CSKV', 'an.nguyen@conganxa.gov.vn', '0987654321'))

        # Viewer User: viewer / viewer123
        cursor.execute("SELECT id FROM users WHERE username = 'viewer'")
        if not cursor.fetchone():
            pass_hash, salt = hash_password("viewer123")
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, full_name, role_id, position, email, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ('viewer', pass_hash, salt, 'Trần Thị Mai', role_map[ROLE_VIEWER], 'Cán bộ văn phòng xã', 'mai.tran@xa.gov.vn', '0933445566'))

        # 4. Seed Areas
        default_areas = [
            ("KHU01", "Khu 1", "Khu vực trung tâm hành chính xã"),
            ("KHU02", "Khu 2", "Khu vực dân cư phía Bắc"),
            ("KHU03", "Khu 3", "Khu vực dân cư phía Nam"),
            ("KHU04", "Khu 4", "Khu vực dân cư phía Đông"),
            ("THON_A", "Thôn A", "Thôn A nông thôn mới"),
            ("THON_B", "Thôn B", "Thôn B làng nghề"),
            ("THON_C", "Thôn C", "Thôn C ven đồi"),
            ("TDP01", "Tổ dân phố 1", "Tổ dân phố phố chợ")
        ]
        for code, name, desc in default_areas:
            cursor.execute("""
                INSERT OR IGNORE INTO areas (code, name, description)
                VALUES (?, ?, ?)
            """, (code, name, desc))

        # 5. Seed System Settings
        default_settings = [
            ("COMMUNE_NAME", "Nông Trang", "Tên Xã / Phường"),
            ("DISTRICT_NAME", "Việt Trì", "Tên Quận / Huyện"),
            ("PROVINCE_NAME", "Phú Thọ", "Tên Tỉnh / Thành phố"),
            ("POLICE_UNIT", "CÔNG AN PHƯỜNG NÔNG TRANG", "Tên đơn vị Công an"),
            ("AUTO_LOCK_MINUTES", "15", "Thời gian tự động khóa màn hình (phút)")
        ]
        for key, val, desc in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO system_settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, val, desc))

        # 6. Seed Sample Population & Household Data if empty
        cursor.execute("SELECT COUNT(*) as count FROM persons")
        if cursor.fetchone()["count"] == 0:
            self._seed_sample_population(cursor)

        conn.commit()
        log_info("Database seeding completed successfully.")

    def _seed_sample_population(self, cursor: sqlite3.Cursor):
        """Seeds realistic sample population and household data for demo purposes."""
        cursor.execute("SELECT id, code FROM areas")
        area_rows = cursor.fetchall()
        area_map = {row["code"]: row["id"] for row in area_rows}

        k1_id = area_map.get("KHU01", 1)
        k2_id = area_map.get("KHU02", 2)
        k3_id = area_map.get("KHU03", 3)
        thona_id = area_map.get("THON_A", 5)

        # Households sample data
        households_data = [
            ("HK000001", "HK-0101", k1_id, "Số 12 đường Trần Hưng Đạo", "Số 12 đường Trần Hưng Đạo, Khu 1, Xã Phú Lương", "2015-05-10"),
            ("HK000002", "HK-0102", k1_id, "Số 45 đường Lý Thường Kiệt", "Số 45 đường Lý Thường Kiệt, Khu 1, Xã Phú Lương", "2016-08-20"),
            ("HK000003", "HK-0201", k2_id, "Xóm 3 Thôn A", "Xóm 3, Thôn A, Xã Phú Lương", "2018-01-15"),
            ("HK000004", "HK-0301", k3_id, "Số 88 đường Lê Lợi", "Số 88 đường Lê Lợi, Khu 3, Xã Phú Lương", "2020-03-12")
        ]

        hh_ids = []
        for code, num, area_id, street, full_addr, reg_date in households_data:
            cursor.execute("""
                INSERT INTO households (household_code, household_number, area_id, address_street, full_address, created_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE')
            """, (code, num, area_id, street, full_addr, reg_date))
            hh_ids.append(cursor.lastrowid)

        # Sample Persons
        sample_persons = [
            # Household 1
            ("NK000001", "Nguyễn Văn Hùng", "1975-04-15", "Nam", "036075001234", "2021-06-10", "Cục CSQLHC về TTXH", "Nam Định", "Kinh", "Việt Nam", "Không", "Kỹ sư xây dựng", "Công ty Xây dựng ABC", "0912111222", "hung.nguyen@gmail.com", "Đã kết hôn", "Số 12 đường Trần Hưng Đạo, Khu 1", "", "Số 12 đường Trần Hưng Đạo, Khu 1", k1_id, "12", "Trần Hưng Đạo", "2015-05-10", "", "Thường trú", "Nguyễn Văn Bình", "036040001111", "Trần Thị Cúc", "", "Phạm Thị Thu", "036178002222", "Chủ hộ", hh_ids[0]),
            ("NK000002", "Phạm Thị Thu", "1978-08-20", "Nữ", "036178002222", "2021-06-10", "Cục CSQLHC về TTXH", "Thái Bình", "Kinh", "Việt Nam", "Không", "Giáo viên", "Trường THCS Phú Lương", "0988222333", "thu.pham@gmail.com", "Đã kết hôn", "Số 12 đường Trần Hưng Đạo, Khu 1", "", "Số 12 đường Trần Hưng Đạo, Khu 1", k1_id, "12", "Trần Hưng Đạo", "2015-05-10", "", "Thường trú", "Phạm Văn Đức", "", "Lê Thị Hồng", "", "Nguyễn Văn Hùng", "036075001234", "Vợ", hh_ids[0]),
            ("NK000003", "Nguyễn Minh Quân", "2005-11-05", "Nam", "036205003333", "2021-12-01", "Cục CSQLHC về TTXH", "Thái Nguyên", "Kinh", "Việt Nam", "Không", "Sinh viên", "Đại học Bách Khoa", "0977333444", "quan.nm@gmail.com", "Độc thân", "Số 12 đường Trần Hưng Đạo, Khu 1", "", "Số 12 đường Trần Hưng Đạo, Khu 1", k1_id, "12", "Trần Hưng Đạo", "2015-05-10", "", "Thường trú", "Nguyễn Văn Hùng", "036075001234", "Phạm Thị Thu", "036178002222", "", "", "Con trai", hh_ids[0]),
            
            # Household 2
            ("NK000004", "Trần Văn Bình", "1968-02-10", "Nam", "036068004444", "2021-05-15", "Cục CSQLHC về TTXH", "Hà Nội", "Kinh", "Việt Nam", "Không", "Kinh doanh", "Cửa hàng vật tư Hùng Bình", "0913444555", "binh.tran@gmail.com", "Đã kết hôn", "Số 45 đường Lý Thường Kiệt, Khu 1", "", "Số 45 đường Lý Thường Kiệt, Khu 1", k1_id, "45", "Lý Thường Kiệt", "2016-08-20", "", "Thường trú", "Trần Văn An", "", "Nguyễn Thị Hòa", "", "Lê Thị Hoa", "036172005555", "Chủ hộ", hh_ids[1]),
            ("NK000005", "Lê Thị Hoa", "1972-09-12", "Nữ", "036172005555", "2021-05-15", "Cục CSQLHC về TTXH", "Thái Nguyên", "Kinh", "Việt Nam", "Phật giáo", "Nội trợ", "Tại gia", "0983555666", "", "Đã kết hôn", "Số 45 đường Lý Thường Kiệt, Khu 1", "", "Số 45 đường Lý Thường Kiệt, Khu 1", k1_id, "45", "Lý Thường Kiệt", "2016-08-20", "", "Thường trú", "Lê Văn Tiến", "", "Hoàng Thị Mơ", "", "Trần Văn Bình", "036068004444", "Vợ", hh_ids[1]),

            # Household 3
            ("NK000006", "Hoàng Văn Nam", "1982-12-01", "Nam", "036082006666", "2022-01-10", "Cục CSQLHC về TTXH", "Thái Nguyên", "Tày", "Việt Nam", "Không", "Nông dân", "Hợp tác xã chè Phú Lương", "0972666777", "", "Đã kết hôn", "Xóm 3, Thôn A", "", "Xóm 3, Thôn A", thona_id, "SN 03", "Xóm 3", "2018-01-15", "", "Thường trú", "Hoàng Văn Thái", "", "Nông Thị Sáu", "", "Nông Thị Phương", "036185007777", "Chủ hộ", hh_ids[2]),

            # Additional individual residents
            ("NK000007", "Đinh Bảo Thành", "1990-07-25", "Nam", "036090008888", "2021-03-20", "Cục CSQLHC về TTXH", "Hải Phòng", "Kinh", "Việt Nam", "Không", "Kế toán", "Công ty Dược phẩm", "0904888999", "thanh.dinh@gmail.com", "Đã kết hôn", "Số 88 đường Lê Lợi, Khu 3", "Số 15 Lê Duẩn, Hà Nội", "Số 88 đường Lê Lợi, Khu 3", k3_id, "88", "Lê Lợi", "2020-03-12", "2023-01-01", "Tạm trú", "Đinh Văn Khánh", "", "Vũ Thị Yến", "", "Bùi Thị Tuyết", "", "Chủ hộ", hh_ids[3]),
            ("NK000008", "Vũ Thị Hương", "1995-04-18", "Nữ", "036195009999", "2022-08-14", "Cục CSQLHC về TTXH", "Bắc Giang", "Kinh", "Việt Nam", "Không", "Y sĩ", "Trạm Y tế xã Phú Lương", "0966999000", "huong.vu@gmail.com", "Độc thân", "Thôn B, Xã Phú Lương", "", "Thôn B, Xã Phú Lương", k2_id, "SN 12", "Thôn B", "2022-08-14", "", "Thường trú", "Vũ Văn Thanh", "", "Đỗ Thị Lài", "", "", "", "Khác", None)
        ]

        person_id_map = {}
        for p in sample_persons:
            p_code, name, dob, gender, id_card, id_date, id_place, hometown, eth, nat, rel, occ, work, phone, email, marital, perm_addr, temp_addr, curr_addr, area_id, house_num, street, perm_reg, temp_reg, res_status, f_name, f_card, m_name, m_card, sp_name, sp_card, rel_head, hh_id = p
            norm_name = vietnamese_unaccent(name)
            
            cursor.execute("""
                INSERT INTO persons (
                    person_code, full_name, normalized_name, dob, gender, id_card_number, id_card_date, id_card_place,
                    hometown, ethnicity, nationality, religion, occupation, workplace, phone, email, marital_status,
                    permanent_address, temporary_address, current_address, area_id, house_number, street_village,
                    permanent_reg_date, temporary_reg_date, residence_status, father_name, father_id_card,
                    mother_name, mother_id_card, spouse_name, spouse_id_card, relationship_with_head, household_id
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                p_code, name, norm_name, dob, gender, id_card, id_date, id_place,
                hometown, eth, nat, rel, occ, work, phone, email, marital,
                perm_addr, temp_addr, curr_addr, area_id, house_num, street,
                perm_reg, temp_reg, res_status, f_name, f_card, m_name, m_card,
                sp_name, sp_card, rel_head, hh_id
            ))
            pid = cursor.lastrowid
            person_id_map[p_code] = pid

            if hh_id:
                cursor.execute("""
                    INSERT INTO household_members (household_id, person_id, relationship, joined_date)
                    VALUES (?, ?, ?, ?)
                """, (hh_id, pid, rel_head, perm_reg))

        # Set household heads
        cursor.execute("UPDATE households SET head_person_id = ? WHERE id = ?", (person_id_map["NK000001"], hh_ids[0]))
        cursor.execute("UPDATE households SET head_person_id = ? WHERE id = ?", (person_id_map["NK000004"], hh_ids[1]))
        cursor.execute("UPDATE households SET head_person_id = ? WHERE id = ?", (person_id_map["NK000006"], hh_ids[2]))
        cursor.execute("UPDATE households SET head_person_id = ? WHERE id = ?", (person_id_map["NK000007"], hh_ids[3]))
