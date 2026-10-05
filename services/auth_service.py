from typing import Optional, Tuple, List
from database.db_manager import DatabaseManager, verify_password
from database.models import User, AuditLog
from utils.logger import log_info, log_error

class AuthService:
    _current_user: Optional[User] = None

    @classmethod
    def login(cls, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """Authenticates user with username and password."""
        if not username or not password:
            return False, "Vui lòng nhập tên đăng nhập và mật khẩu.", None

        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT u.*, r.role_code, r.role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ?
            """
            cursor.execute(sql, (username.strip(),))
            row = cursor.fetchone()
            if not row:
                return False, "Tài khoản hoặc mật khẩu không chính xác.", None

            if not row["is_active"]:
                return False, "Tài khoản hiện đang bị khóa hoặc ngưng hoạt động.", None

            # Verify password hash
            if not verify_password(password, row["password_hash"], row["salt"]):
                # Update failed login count
                cursor.execute(
                    "UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE id = ?",
                    (row["id"],)
                )
                conn.commit()
                return False, "Tài khoản hoặc mật khẩu không chính xác.", None

            # Fetch user permissions
            perm_sql = "SELECT permission_code FROM permissions WHERE role_id = ?"
            cursor.execute(perm_sql, (row["role_id"],))
            perms = [p["permission_code"] for p in cursor.fetchall()]

            user = User.from_row(row, permissions=perms)
            cls._current_user = user

            # Reset failed login count & update last_login
            cursor.execute(
                "UPDATE users SET failed_login_attempts = 0, last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user.id,)
            )
            conn.commit()

            # Record audit log safely
            cls.log_audit_action("LOGIN", "USER", user.id, f"Người dùng '{user.username}' ({user.full_name}) đăng nhập hệ thống thành công.")
            log_info(f"User '{user.username}' logged in successfully.")

            return True, "Đăng nhập thành công!", user
        except Exception as e:
            log_error(f"Login error for user {username}: {e}", exc_info=True)
            return False, f"Lỗi hệ thống khi đăng nhập: {e}", None
        finally:
            conn.close()

    @classmethod
    def logout(cls):
        """Logs out current user."""
        if cls._current_user:
            cls.log_audit_action("LOGOUT", "USER", cls._current_user.id, f"Người dùng '{cls._current_user.username}' đăng xuất.")
            cls._current_user = None

    @classmethod
    def get_current_user(cls) -> Optional[User]:
        """Returns logged-in User instance."""
        return cls._current_user

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._current_user is not None

    @classmethod
    def check_permission(cls, perm_code: str) -> bool:
        if not cls._current_user:
            return False
        return cls._current_user.has_permission(perm_code)

    @classmethod
    def log_audit_action(cls, action: str, target_type: str = "", target_id: Optional[int] = None, details: str = ""):
        """
        Inserts audit log into database without exposing sensitive data.
        """
        user = cls._current_user
        username = user.username if user else "SYSTEM"
        user_id = user.id if user else None

        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO audit_logs (user_id, username, action, target_type, target_id, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, action, target_type, target_id, details))
            conn.commit()
        except Exception as e:
            log_error(f"Error logging audit action: {e}")
        finally:
            conn.close()
