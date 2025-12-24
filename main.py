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
    cancel,
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
    # Create the Application builder
    builder = Application.builder().token(BOT_TOKEN).post_init(post_init)
    
    
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
                CommandHandler("card", handle_card_number),
                CommandHandler("link", handle_donation_link),
                CommandHandler("amount", handle_donation_amount),
                CommandHandler("upload", handle_payment_upload),
                CommandHandler("history", handle_payment_history),
                CommandHandler("cancel", cancel),
                MessageHandler(filters.TEXT, show_main_menu),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Start the Bot
    application.run_polling()


if __name__ == "__main__":
    main()
