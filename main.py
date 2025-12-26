"""Main bot application."""

import logging
from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    JobQueue,
)
from telegram import Update
from telegram.ext import ContextTypes
from telegram.request import HTTPXRequest
import pytz
from datetime import time

from aharar_bot.config import BOT_TOKEN, TIMEZONE
from aharar_bot.handlers import (
    start,
    handle_pin_code,
    handle_verification,
    show_main_menu,
    handle_card_number,
    handle_donation_link,
    handle_donation_amount,
    handle_payment_upload,
    handle_payment_history,
    handle_pending_admin_broadcast,
    handle_protected_command,
    cancel,
    logout,
    report_command,
    broadcast_command,
    manual_trigger,
    # Debug/admin helpers
    log_update,
    global_error_handler,
    PIN_CODE,
    VERIFICATION,
    MAIN_MENU,
)
from aharar_bot.scheduler import (
    send_donation_notification,
    send_reminder_notification,
    send_monthly_report,
    handle_payment_approval,
    handle_payment_denial,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def handle_callback_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("approve_"):
        payment_id = int(data.split("_")[1])
        await handle_payment_approval(update, context, payment_id)
        await query.edit_message_text(text="پرداخت تأیید شد ✅")

    elif data.startswith("deny_"):
        payment_id = int(data.split("_")[1])
        await handle_payment_denial(update, context, payment_id)
        await query.edit_message_text(text="پرداخت رد شد ❌")


async def post_init(application: Application) -> None:
    """Post initialization tasks."""
    job_queue: JobQueue = application.job_queue

    if job_queue is None:
        logger.warning(
            "JobQueue is not available. To enable scheduled tasks, install the job-queue extras: pip install \"python-telegram-bot[job-queue]\" and rebuild the image."
        )
        return

    # Schedule notification on 3rd of each month at 9:00 AM
    job_queue.run_daily(
        send_donation_notification,
        time=time(hour=9, minute=0, tzinfo=pytz.timezone(TIMEZONE)),
    )

    # Schedule reminder on 7th of each month at 9:00 AM
    job_queue.run_daily(
        send_reminder_notification,
        time=time(hour=9, minute=0, tzinfo=pytz.timezone(TIMEZONE)),
    )

    # Schedule report on 10th of each month at 8:00 PM
    job_queue.run_daily(
        send_monthly_report,
        time=time(hour=20, minute=0, tzinfo=pytz.timezone(TIMEZONE)),
    )


def main() -> None:
    """Start the bot."""
    # Create the Application builder with increased timeouts for unreliable networks
    request = HTTPXRequest(
        connect_timeout=20,  # Increased from default 5s
        read_timeout=20,     # Increased from default 5s
        write_timeout=20,    # Increased from default 5s
        pool_timeout=20      # Increased from default 5s
    )
    
    builder = Application.builder().token(BOT_TOKEN).request(request).post_init(post_init)
    
    application = builder.build()

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PIN_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pin_code)],
            VERIFICATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification)
            ],
            MAIN_MENU: [
                CommandHandler("start", start),
                CommandHandler("cancel", cancel),
                # Catch pending broadcast messages in interactive mode
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pending_admin_broadcast),
                # Avoid matching slash commands as plain text; only handle non-command text
                MessageHandler(filters.TEXT & ~filters.COMMAND, show_main_menu),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Global pre-handler for pending admin interactive broadcast messages (moved inside MAIN_MENU to avoid blocking PIN entry)
    # Removed from group 0 to avoid interfering with conversation states

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Global error handler to surface exceptions and notify admin
    application.add_error_handler(global_error_handler)

    # Accept photos directly from verified users (also supports /upload flow)
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment_upload))

    # Admin and utility commands
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("manual_trigger", manual_trigger))

    # Register protected user commands globally but enforce verification first
    application.add_handler(CommandHandler("card", handle_protected_command))
    application.add_handler(CommandHandler("link", handle_protected_command))
    application.add_handler(CommandHandler("amount", handle_protected_command))
    application.add_handler(CommandHandler("upload", handle_protected_command))
    application.add_handler(CommandHandler("history", handle_protected_command))

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
