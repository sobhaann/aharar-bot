"""Configuration module for Aharar Charity Bot."""

import os
from typing import Final

# Bot Configuration
BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "your_bot_token_here")
ADMIN_CHAT_ID: Final[int] = int(os.getenv("ADMIN_CHAT_ID", "0"))
ADMIN_USERNAME: Final[str] = "@Ahrarcharity_admin"


# Database Configuration
DATABASE_PATH: Final[str] = os.getenv("DATABASE_PATH", "aharar_bot.db")
SEED_DATA_PATH: Final[str] = os.getenv("SEED_DATA_PATH", "./data/seed_data.csv")

# Timezone Configuration
TIMEZONE: Final[str] = "Asia/Tehran"

# Jalali Calendar Months (Persian Month Names)
JALALI_MONTHS: dict[int, str] = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند",
}

# Notification Days (Jalali Calendar)
NOTIFICATION_DAY: Final[int] = 3  # 3rd of each month
REMINDER_DAY: Final[int] = 7  # 7th of each month
REPORT_DAY: Final[int] = 10  # 10th of each month

# Payment Status
class PaymentStatus:
    """Payment status constants."""
    PENDING: Final[str] = "pending"
    APPROVED: Final[str] = "approved"
    FAILED: Final[str] = "failed"

# User Status
class UserStatus:
    """User status constants."""
    UNVERIFIED: Final[str] = "unverified"
    VERIFIED: Final[str] = "verified"
    PENDING_ADMIN: Final[str] = "pending_admin"
