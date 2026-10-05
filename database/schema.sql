-- Enable Foreign Key Constraints
PRAGMA foreign_keys = ON;

-- 1. Table: areas (Khu vực / Thôn / Tổ dân phố)
CREATE TABLE IF NOT EXISTS areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table: households (Hộ gia đình)
CREATE TABLE IF NOT EXISTS households (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_code TEXT UNIQUE NOT NULL,
    household_number TEXT,
    area_id INTEGER NOT NULL,
    head_person_id INTEGER,
    address_street TEXT,
    full_address TEXT,
    created_date DATE,
    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, MOVED, SPLIT, ARCHIVED
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE RESTRICT
);

-- 3. Table: persons (Thông tin nhân khẩu)
CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_code TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    normalized_name TEXT,
    dob DATE,
    gender TEXT,
    id_card_number TEXT,
    id_card_date DATE,
    id_card_place TEXT,
    hometown TEXT,
    ethnicity TEXT DEFAULT 'Kinh',
    nationality TEXT DEFAULT 'Việt Nam',
    religion TEXT DEFAULT 'Không',
    occupation TEXT,
    workplace TEXT,
    phone TEXT,
    email TEXT,
    marital_status TEXT,
    permanent_address TEXT,
    temporary_address TEXT,
    current_address TEXT,
    area_id INTEGER NOT NULL,
    house_number TEXT,
    street_village TEXT,
    permanent_reg_date DATE,
    temporary_reg_date DATE,
    residence_status TEXT DEFAULT 'Thường trú', -- Thường trú, Tạm trú, Tạm vắng, Chuyển đi, Đã mất
    father_name TEXT,
    father_id_card TEXT,
    mother_name TEXT,
    mother_id_card TEXT,
    spouse_name TEXT,
    spouse_id_card TEXT,
    relationship_with_head TEXT,
    household_id INTEGER,
    avatar_path TEXT,
    notes TEXT,
    is_deleted INTEGER DEFAULT 0,
    deleted_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER,
    FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE RESTRICT,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE SET NULL
);

-- Add Foreign Key for head_person_id in households (after persons table creation)
-- SQLite foreign keys check on insert/update.

-- 4. Table: household_members (Liên kết hộ gia đình - nhân khẩu)
CREATE TABLE IF NOT EXISTS household_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    relationship TEXT NOT NULL,
    joined_date DATE,
    leave_date DATE,
    status TEXT DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (household_id) REFERENCES households(id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
    UNIQUE(household_id, person_id)
);

-- 5. Table: roles (Vai trò)
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code TEXT UNIQUE NOT NULL,
    role_name TEXT NOT NULL,
    description TEXT
);

-- 6. Table: permissions (Quyền hạn)
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_code TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_code)
);

-- 7. Table: users (Tài khoản người dùng)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    position TEXT,
    email TEXT,
    phone TEXT,
    is_active INTEGER DEFAULT 1,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until DATETIME,
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- 8. Table: audit_logs (Nhật ký thao tác)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id INTEGER,
    details TEXT NOT NULL,
    ip_address TEXT DEFAULT '127.0.0.1',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 9. Table: import_history (Lịch sử Nhập liệu Excel)
CREATE TABLE IF NOT EXISTS import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    total_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    imported_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_log TEXT,
    FOREIGN KEY (imported_by) REFERENCES users(id)
);

-- 10. Table: system_settings (Cài đặt hệ thống)
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES for performance optimization
CREATE INDEX IF NOT EXISTS idx_persons_normalized_name ON persons(normalized_name);
CREATE INDEX IF NOT EXISTS idx_persons_area_id ON persons(area_id);
CREATE INDEX IF NOT EXISTS idx_persons_household_id ON persons(household_id);
CREATE INDEX IF NOT EXISTS idx_persons_residence_status ON persons(residence_status);
CREATE INDEX IF NOT EXISTS idx_persons_is_deleted ON persons(is_deleted);
CREATE INDEX IF NOT EXISTS idx_persons_id_card ON persons(id_card_number);

CREATE INDEX IF NOT EXISTS idx_households_area_id ON households(area_id);
CREATE INDEX IF NOT EXISTS idx_households_status ON households(status);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
