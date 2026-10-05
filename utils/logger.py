import logging
import os
from datetime import datetime
from config import LOG_DIR

# Set up standard logger
log_file = LOG_DIR / f"app_{datetime.now().strftime('%Y%m')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("PopulationManager")

def log_info(msg: str):
    logger.info(msg)

def log_warning(msg: str):
    logger.warning(msg)

def log_error(msg: str, exc_info=False):
    logger.error(msg, exc_info=exc_info)
