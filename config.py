import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
STYLES_DIR = ASSETS_DIR / "styles"
AVATARS_DIR = ASSETS_DIR / "avatars"

# Create required directories
for d in [DATA_DIR, BACKUP_DIR, LOG_DIR, ASSETS_DIR, ICONS_DIR, STYLES_DIR, AVATARS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database config
DB_PATH = DATA_DIR / "population.db"

# Application Metadata
APP_NAME = "HỆ THỐNG QUẢN LÝ NHÂN KHẨU CẤP XÃ"
APP_SUBTITLE = "CÔNG AN PHƯỜNG NÔNG TRANG"
APP_VERSION = "1.0.0"
ORGANIZATION_NAME = "Công an Phường Nông Trang"

# Security Settings
AUTO_LOCK_MINUTES = 15
MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION_MINUTES = 15

# Color Palette (GOV Vietnam Style)
COLOR_PRIMARY_BURGUNDY = "#A6192E"
COLOR_SECONDARY_DARK_RED = "#8B0000"
COLOR_NAVY_SIDEBAR = "#17365D"
COLOR_NAVY_DARK = "#0F2440"
COLOR_BG_LIGHT = "#F4F6F9"
COLOR_WHITE = "#FFFFFF"
COLOR_SUCCESS_GREEN = "#198754"
COLOR_WARNING_ORANGE = "#F39C12"
COLOR_DANGER_RED = "#DC3545"
COLOR_INFO_BLUE = "#0D6EFD"
COLOR_TEXT_MAIN = "#212529"
COLOR_TEXT_MUTED = "#6C757D"
COLOR_BORDER = "#DEE2E6"
