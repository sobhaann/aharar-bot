"""Utility functions for Aharar Charity Bot."""

from datetime import datetime
import pytz

from .config import TIMEZONE, JALALI_MONTHS


import jdatetime

class JalaliCalendar:
    """Jalali (Persian) calendar utilities using jdatetime."""

    @staticmethod
    def gregorian_to_jalali(gregorian_date: datetime) -> tuple[int, int, int]:
        """Convert Gregorian datetime to Jalali (j_y, j_m, j_d)."""
        jd = jdatetime.datetime.fromgregorian(datetime=gregorian_date)
        return jd.year, jd.month, jd.day

    @staticmethod
    def jalali_to_gregorian(j_y: int, j_m: int, j_d: int) -> datetime:
        """Convert Jalali date to Gregorian datetime."""
        jd = jdatetime.date(j_y, j_m, j_d)
        gd = jd.togregorian()
        return datetime(gd.year, gd.month, gd.day)

    @staticmethod
    def get_current_jalali_date() -> tuple[int, int, int]:
        """Get current date in Jalali calendar (year, month, day)."""
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        return JalaliCalendar.gregorian_to_jalali(now)

    @staticmethod
    def get_current_jalali_month_year() -> tuple[int, int]:
        """Get current month and year in Jalali calendar (month, year)."""
        j_y, j_m, _ = JalaliCalendar.get_current_jalali_date()
        return j_m, j_y

    @staticmethod
    def format_jalali_date(j_y: int, j_m: int, j_d: int) -> str:
        """Format Jalali date as string."""
        month_name = JALALI_MONTHS.get(j_m, "نامشخص")
        return f"{j_d} {month_name} {j_y}"


def normalize_pin(pin: str) -> str:
    """Normalize PIN/identifier input.

    - Strips whitespace
    - Replaces Persian and Arabic-Indic numerals with ASCII digits
    - Removes zero-width spaces and control characters
    """
    if not pin:
        return ""

    # strip and remove zero-width/control characters
    s = pin.strip()
    s = s.replace("\u200c", "")  # zero-width non-joiner
    s = s.replace("\u200b", "")  # zero-width space

    # Maps for Persian and Arabic-Indic digits
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"

    result_chars: list[str] = []
    for ch in s:
        if ch in persian_digits:
            result_chars.append(str(persian_digits.index(ch)))
        elif ch in arabic_digits:
            result_chars.append(str(arabic_digits.index(ch)))
        else:
            result_chars.append(ch)

    normalized = "".join(result_chars)
    # final strip of whitespace
    return normalized.strip()


class MessageFormatter:
    """Message formatting utilities."""

    @staticmethod
    def format_donation_reminder(
        full_name: str, amount: str, donation_link: str
    ) -> str:
        """Format donation reminder message."""
        return (
            f"{full_name} عزیز سلام\n"
            f"موعد پرداخت {amount} تومان این ماه فرا رسیده\n"
            f"لینک پرداخت:\n{donation_link}\n"
            f"شماره کارت خیریه (با لمس کردن کپی می شود):\n"
            f"۶۲۲۱۰۶۱۲۳۷۷۵۷۰۸۵ - مهدی شاعری\n"
            f"در صورت واریز وجه، رسید آنرا از طریق آپلود بفرستید"
        )

    @staticmethod
    def format_pin_request() -> str:
        """Format pin request message."""
        return "سلام\nلطفا کد معرف‌تون رو بفرستید (مثلا 021)"

    @staticmethod
    def format_invalid_pin() -> str:
        """Format invalid pin message."""
        return (
            "کد شما یافت نشد!\n"
            "لطفا یک کد معرف معتبر ارسال کنید\n"
            "(مطمئن شوید کیبورد شما روی زبان انگلیسی است)"
        )

    @staticmethod
    def format_verification_request(full_name: str) -> str:
        """Format verification request message."""
        return f"شما {full_name} هستید؟"

    @staticmethod
    def format_success_message(
        donation_link: str, amount: str, card_number: str = "۶۲۲۱۰۶۱۲۳۷۷۵۷۰۸۵"
    ) -> str:
        """Format success message after verification."""
        return (
            "اطلاعات شما با موفقیت ثبت شد\n\n"
        )

    @staticmethod
    def format_payment_approved() -> str:
        """Format payment approved message."""
        return (
            "پرداخت شما با موفقیت تأیید شد!\n"
            "برای کمک شما سپاسگزارم."
        )

    @staticmethod
    def format_payment_denied() -> str:
        """Format payment denied message."""
        return (
            "متأسفانه پرداخت شما تأیید نشد.\n"
            f"لطفا با ادمین (@Ahrarcharity_admin) تماس بگیرید."
        )


def get_next_notification_day(target_day: int) -> tuple[int, int, int]:
    """
    Get the next occurrence of a specific day in Jalali calendar.

    Args:
        target_day: Target day of month (1-31)

    Returns:
        Tuple of (year, month, day) in Jalali calendar
    """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    current_year, current_month, current_day = JalaliCalendar.gregorian_to_jalali(
        now
    )

    if current_day <= target_day:
        return current_year, current_month, target_day
    else:
        # Move to next month
        next_month = current_month + 1
        next_year = current_year

        if next_month > 12:
            next_month = 1
            next_year += 1

        return next_year, next_month, target_day
