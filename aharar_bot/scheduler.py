"""Scheduler tasks for notifications and reports."""

import os
from datetime import datetime
import pytz
from pathlib import Path
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from telegram.ext import ContextTypes

from .database import Database
from .config import TIMEZONE, NOTIFICATION_DAY, REMINDER_DAY, REPORT_DAY, UserStatus, PaymentStatus, ADMIN_CHAT_ID, JALALI_MONTHS
from .utils import JalaliCalendar, MessageFormatter

db = Database()


async def send_donation_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send donation notification on the 3rd of each month."""
    j_m, j_y = JalaliCalendar.get_current_jalali_month_year()
    
    # Only send if today is the notification day
    _, _, current_day = JalaliCalendar.get_current_jalali_date()
    if current_day != NOTIFICATION_DAY:
        return

    verified_users = db.get_all_verified_users()
    
    for user in verified_users:
        if not user.get("telegram_id"):
            continue

        message = MessageFormatter.format_donation_reminder(
            user["full_name"],
            user["donation_amount"],
            user["donation_link"],
        )

        try:
            await context.bot.send_message(user["telegram_id"], message)
        except Exception as e:
            print(f"Error sending notification to {user['full_name']}: {e}")


async def send_reminder_notification(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send reminder notification for pending payments on the 7th of each month."""
    j_m, j_y = JalaliCalendar.get_current_jalali_month_year()
    
    # Only send if today is the reminder day
    _, _, current_day = JalaliCalendar.get_current_jalali_date()
    if current_day != REMINDER_DAY:
        return

    pending_payments = db.get_pending_payments(j_m, j_y)
    
    for payment in pending_payments:
        user = db.get_user_by_id(payment["user_id"])
        if not user or not user.get("telegram_id"):
            continue

        message = (
            f"{user['full_name']} عزیز\n\n"
            f"متاسفانه پرداخت {user['donation_amount']} تومانی شما هنوز ثبت نشده است.\n"
            f"لطفا در اسرع وقت درخواست خود را انجام دهید.\n\n"
            f"لینک پرداخت: {user['donation_link']}"
        )

        try:
            await context.bot.send_message(user["telegram_id"], message)
        except Exception as e:
            print(f"Error sending reminder to {user['full_name']}: {e}")


async def send_monthly_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send monthly report (Excel and PDF) on the 10th of each month."""
    _, _, current_day = JalaliCalendar.get_current_jalali_date()
    if current_day != REPORT_DAY:
        return

    j_m, j_y = JalaliCalendar.get_current_jalali_month_year()
    
    # Get monthly summary
    summary = db.get_monthly_summary(j_m, j_y)
    
    # Create Excel file
    excel_path = await create_excel_report(summary)
    
    # Create PDF file
    pdf_path = await create_pdf_report(summary)
    
    # Send files to admin
    try:
        with open(excel_path, "rb") as excel_file:
            await context.bot.send_document(
                ADMIN_CHAT_ID,
                excel_file,
                filename=f"گزارش_ماه_{j_m}_{j_y}.xlsx",
            )

        with open(pdf_path, "rb") as pdf_file:
            await context.bot.send_document(
                ADMIN_CHAT_ID,
                pdf_file,
                filename=f"گزارش_ماه_{j_m}_{j_y}.pdf",
            )
    except Exception as e:
        print(f"Error sending monthly report: {e}")
    finally:
        # Clean up files
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


async def create_excel_report(summary: dict) -> str:
    """Create Excel report."""
    j_m = summary["month"]
    j_y = summary["year"]
    
    excel_path = f"reports/monthly_report_{j_y}_{j_m}.xlsx"
    Path("reports").mkdir(exist_ok=True)
    
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = f"ماه {j_m}"
    
    # Add headers
    headers = ["نام و نام خانوادگی", "مبلغ تعهدی", "وضعیت پرداخت"]
    worksheet.append(headers)
    
    # Add data
    for row in summary["data"]:
        worksheet.append([
            row["full_name"],
            row["donation_amount"],
            row["payment_status"],
        ])
    
    # Adjust column widths
    worksheet.column_dimensions["A"].width = 30
    worksheet.column_dimensions["B"].width = 15
    worksheet.column_dimensions["C"].width = 15
    
    workbook.save(excel_path)
    return excel_path


async def create_pdf_report(summary: dict) -> str:
    """Create PDF report."""
    j_m = summary["month"]
    j_y = summary["year"]
    
    pdf_path = f"reports/monthly_report_{j_y}_{j_m}.pdf"
    Path("reports").mkdir(exist_ok=True)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=72, leftMargin=72)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Add title
    title = Paragraph(f"گزارش ماهانه - ماه {j_m} سال {j_y}", styles["Heading1"])
    story.append(title)
    
    # Create table data
    table_data = [["نام و نام خانوادگی", "مبلغ تعهدی", "وضعیت پرداخت"]]
    for row in summary["data"]:
        table_data.append([
            row["full_name"],
            row["donation_amount"],
            row["payment_status"],
        ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(table)
    
    doc.build(story)
    return pdf_path


async def handle_payment_approval(
    update, context: ContextTypes.DEFAULT_TYPE, payment_id: int
) -> None:
    """Handle payment approval."""
    payment = db.conn.cursor().execute(
        "SELECT * FROM payments WHERE id = ?", (payment_id,)
    ).fetchone()
    
    if not payment:
        return
    
    user = db.get_user_by_id(payment["user_id"])
    if not user:
        return
    
    # Update payment status
    db.update_payment_status(payment_id, PaymentStatus.APPROVED)
    
    # Notify user
    if user.get("telegram_id"):
        message = MessageFormatter.format_payment_approved()
        await context.bot.send_message(user["telegram_id"], message)


async def handle_payment_denial(
    update, context: ContextTypes.DEFAULT_TYPE, payment_id: int
) -> None:
    """Handle payment denial."""
    payment = db.conn.cursor().execute(
        "SELECT * FROM payments WHERE id = ?", (payment_id,)
    ).fetchone()
    
    if not payment:
        return
    
    user = db.get_user_by_id(payment["user_id"])
    if not user:
        return
    
    # Update payment status
    db.update_payment_status(payment_id, PaymentStatus.FAILED)
    
    # Notify user
    if user.get("telegram_id"):
        message = MessageFormatter.format_payment_denied()
        await context.bot.send_message(user["telegram_id"], message)
