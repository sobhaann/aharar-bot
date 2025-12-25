"""Handlers for user interactions."""

from typing import Optional
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from .database import Database
from .config import UserStatus, PaymentStatus, ADMIN_CHAT_ID
from .models import UserModel
from .utils import MessageFormatter, JalaliCalendar
import logging

logger = logging.getLogger(__name__)

# Conversation states
PIN_CODE = 0
VERIFICATION = 1
MAIN_MENU = 2

db = Database()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command handler."""
    user = update.effective_user
    telegram_id = user.id

    # Check if user already verified
    existing_user = db.get_user_by_telegram_id(telegram_id)
    if existing_user:
        if existing_user["status"] == UserStatus.VERIFIED:
            await show_main_menu(update, context)
            return MAIN_MENU
        elif existing_user["status"] == UserStatus.PENDING_ADMIN:
            await update.message.reply_text(
                "حساب شما در انتظار تأیید مدیر است.\nلطفا بعداً دوباره تلاش کنید."
            )
            return ConversationHandler.END

    # Request PIN code
    await update.message.reply_text(MessageFormatter.format_pin_request())
    return PIN_CODE


async def handle_pin_code(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle PIN code input."""
    pin_code = update.message.text.strip()

    # Normalize and validate pin code
    from .utils import normalize_pin

    normalized = normalize_pin(pin_code)
    logger.debug("PIN input: %s normalized: %s", pin_code, normalized)

    user = db.get_user_by_pin(normalized)

    # Fallback: if numeric and not found, try matching by numeric value ignoring leading zeros
    if not user and normalized.isdigit():
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        for row in rows:
            db_pin = (row["pin_code"] or "").strip()
            try:
                if db_pin.isdigit() and int(db_pin) == int(normalized):
                    user = dict(row)
                    break
            except ValueError:
                continue

    if not user:
        await update.message.reply_text(MessageFormatter.format_invalid_pin())
        return PIN_CODE

    # Store user data in context
    context.user_data["user_pin"] = pin_code
    context.user_data["user_id"] = user["id"]
    context.user_data["full_name"] = user["full_name"]
    context.user_data["donation_link"] = user["donation_link"]
    context.user_data["donation_amount"] = user["donation_amount"]

    # Request verification
    verification_msg = MessageFormatter.format_verification_request(user["full_name"])
    reply_keyboard = [["بله", "خیر"]]
    await update.message.reply_text(
        verification_msg,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return VERIFICATION


async def handle_verification(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle user verification."""
    response = update.message.text.strip()

    if response == "بله":
        user_id = context.user_data["user_id"]
        telegram_id = update.effective_user.id
        full_name = context.user_data["full_name"]

        # Update user with Telegram ID
        db.update_user_telegram_id(user_id, telegram_id, UserStatus.VERIFIED)

        # Send success message
        success_msg = MessageFormatter.format_success_message(
            context.user_data["donation_link"], context.user_data["donation_amount"]
        )
        await update.message.reply_text(
            success_msg, reply_markup=ReplyKeyboardRemove()
        )

        # Show main menu
        await show_main_menu(update, context)
        return MAIN_MENU

    elif response == "خیر":
        # Reset and ask for PIN again
        await update.message.reply_text(
            MessageFormatter.format_pin_request(),
            reply_markup=ReplyKeyboardRemove(),
        )
        return PIN_CODE

    return VERIFICATION


async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Show main menu."""
    menu_text = (
        "منوی اصلی:\n\n"
        "/card - شماره کارت خیریه\n"
        "/link - لینک پرداخت\n"
        "/amount - مبلغ تعهدی من\n"
        "/upload - آپلود فیش واریزی\n"
        "/history - سابقه پرداخت‌های من"
    )
    # Use slash commands so pressing buttons triggers CommandHandlers
    reply_keyboard = [
        ["/card", "/link"],
        ["/amount", "/upload"],
        ["/history"],
    ]
    await update.message.reply_text(
        menu_text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, selective=True
        ),
    )
    return MAIN_MENU


async def handle_card_number(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle card number request."""
    card_number = "۶۲۲۱۰۶۱۲۳۷۷۵۷۰۸۵"
    await update.message.reply_text(
        f"شماره کارت خیریه (با لمس کردن کپی می شود):\n`{card_number}`",
        parse_mode="Markdown",
    )


async def handle_donation_link(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle donation link request."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text(
            f"لینک پرداخت شما:\n{user['donation_link']}"
        )
    else:
        await update.message.reply_text("کاربری یافت نشد.")


async def handle_donation_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle donation amount request."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text(
            f"مبلغ تعهدی شما: {user['donation_amount']} تومان"
        )
    else:
        await update.message.reply_text("کاربری یافت نشد.")


async def handle_payment_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int | None:
    """Handle payment image upload.

    Supports both `/upload` command (prompts for a photo) and direct photo
    messages (process immediately) from verified users.
    """
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("کاربری یافت نشد.")
        return MAIN_MENU

    # If command invoked without a photo, prompt user to send one
    if not update.message.photo:
        # mark waiting state for next photo (optional)
        context.user_data["awaiting_photo"] = True
        await update.message.reply_text("لطفا یک تصویر ارسال کنید.")
        return MAIN_MENU

    # If a photo is provided (directly or after prompt), process it
    # Clear awaiting flag
    context.user_data.pop("awaiting_photo", None)

    # Get the highest quality photo
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    # Ensure payments directory exists
    import os
    os.makedirs("payments", exist_ok=True)

    # Save photo
    file_path = f"payments/{user['id']}_{photo.file_id}.jpg"
    await file.download_to_drive(file_path)

    # Create payment record
    j_m, j_y = JalaliCalendar.get_current_jalali_month_year()
    payment_id = db.create_payment(user["id"], j_m, j_y, PaymentStatus.PENDING)

    # Notify admin (ensure ADMIN_CHAT_ID is configured)
    if not ADMIN_CHAT_ID or ADMIN_CHAT_ID == 0:
        logger.error("ADMIN_CHAT_ID not configured; cannot notify admin of payment %s", payment_id)
        await update.message.reply_text(
            "تصویر با موفقیت ارسال شد؛ اما ادمین پیکربندی نشده است. لطفا صبور باشید."
        )
        return MAIN_MENU

    admin_msg = (
        f"پرداخت جدید برای تأیید:\n\n"
        f"نام: {user['full_name']}\n"
        f"مبلغ: {user['donation_amount']}\n"
        f"شناسه پرداخت: {payment_id}"
    )

    await context.bot.send_message(ADMIN_CHAT_ID, admin_msg)
    await context.bot.send_photo(ADMIN_CHAT_ID, photo.file_id)

    # Add inline buttons for admin approval
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = [
        [
            InlineKeyboardButton("تأیید", callback_data=f"approve_{payment_id}"),
            InlineKeyboardButton("رد کردن", callback_data=f"deny_{payment_id}"),
        ]
    ]
    await context.bot.send_message(
        ADMIN_CHAT_ID,
        "لطفا تصویر را تأیید یا رد کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    await update.message.reply_text(
        "تصویر شما با موفقیت ارسال شد.\nانتظار تأیید مدیر..."
    )

    return MAIN_MENU


async def handle_payment_history(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle payment history request."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("کاربری یافت نشد.")
        return

    # Get payment history
    cursor = db.conn.cursor()
    cursor.execute(
        """
        SELECT jalali_month, jalali_year, status FROM payments
        WHERE user_id = ?
        ORDER BY jalali_year DESC, jalali_month DESC
        """,
        (user["id"],),
    )
    payments = cursor.fetchall()

    if not payments:
        await update.message.reply_text("سابقه‌ای برای شما وجود ندارد.")
        return

    history_text = "سابقه پرداخت‌های من:\n\n"
    for payment in payments:
        month_name = JalaliCalendar.format_jalali_date(payment[1], payment[0], 1)
        status_text = {
            PaymentStatus.APPROVED: "✅ تأیید شده",
            PaymentStatus.PENDING: "⏳ در انتظار",
            PaymentStatus.FAILED: "❌ رد شده",
        }.get(payment[2], "نامشخص")

        history_text += f"{month_name}: {status_text}\n"

    await update.message.reply_text(history_text)


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Logout the current user (disassociate Telegram ID)."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        # Use reply_markup to ensure this is sent as a reply; handle clients that don't support reply_text return value
        await update.message.reply_text("شما در سیستم وارد نشده‌اید.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    db.logout_user_by_telegram_id(telegram_id)
    # Clear any per-user session data and remove keyboard
    context.user_data.clear()
    await update.message.reply_text("شما با موفقیت از حساب خارج شدید.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to view current month's payment statuses."""
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("فقط ادمین می‌تواند این دستور را اجرا کند.")
        return

    j_m, j_y = JalaliCalendar.get_current_jalali_month_year()
    summary = db.get_monthly_summary(j_m, j_y)

    msg_lines = [f"گزارش ماه {j_m} سال {j_y}:\n"]
    for row in summary["data"]:
        status = row.get("payment_status")
        emoji = "✅" if status == PaymentStatus.APPROVED else "❌"
        msg_lines.append(f"{emoji} {row['full_name']} — {row['donation_amount']}")

    await update.message.reply_text("\n".join(msg_lines))


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to broadcast a message to all verified users.

    Usage: /broadcast This is the message
    """
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("فقط ادمین می‌تواند این دستور را اجرا کند.")
        return

    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("استفاده: /broadcast پیام شما")
        return

    users = db.get_all_verified_users()
    sent = 0
    for user in users:
        if not user.get("telegram_id"):
            continue
        try:
            await context.bot.send_message(user["telegram_id"], text)
            sent += 1
        except Exception as e:
            logger.error("Failed to send broadcast to %s: %s", user['full_name'], e)

    await update.message.reply_text(f"پیام شما به {sent} کاربر ارسال شد.")


async def manual_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to manually trigger scheduled tasks.

    Usage: /manual_trigger donation|reminder|report
    """
    if update.effective_user.id != ADMIN_CHAT_ID:
        await update.message.reply_text("فقط ادمین می‌تواند این دستور را اجرا کند.")
        return

    if not context.args:
        await update.message.reply_text("استفاده: /manual_trigger donation|reminder|report")
        return

    cmd = context.args[0].lower()
    if cmd == "donation":
        await send_donation_notification(context)
        await update.message.reply_text("اعلان‌های پرداخت ارسال شد.")
    elif cmd == "reminder":
        await send_reminder_notification(context)
        await update.message.reply_text("اعلان‌های یادآوری ارسال شد.")
    elif cmd == "report":
        # Generate and send report immediately (bypass date check)
        j_m, j_y = JalaliCalendar.get_current_jalali_month_year()
        summary = db.get_monthly_summary(j_m, j_y)
        from .scheduler import create_excel_report, create_pdf_report

        excel_path = await create_excel_report(summary)
        pdf_path = await create_pdf_report(summary)

        try:
            with open(excel_path, "rb") as excel_file:
                await context.bot.send_document(ADMIN_CHAT_ID, excel_file, filename=f"گزارش_ماه_{j_m}_{j_y}.xlsx")
            with open(pdf_path, "rb") as pdf_file:
                await context.bot.send_document(ADMIN_CHAT_ID, pdf_file, filename=f"گزارش_ماه_{j_m}_{j_y}.pdf")
            await update.message.reply_text("گزارش ماهانه ارسال شد.")
        finally:
            import os
            if os.path.exists(excel_path):
                os.remove(excel_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    else:
        await update.message.reply_text("گزینه نامعتبر. از donation|reminder|report استفاده کنید.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel handler."""
    await update.message.reply_text(
        "عملیات لغو شد.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
