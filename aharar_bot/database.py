"""Database module for Aharar Charity Bot."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import csv

from .config import DATABASE_PATH, SEED_DATA_PATH, PaymentStatus, UserStatus


class Database:
    """Database management class."""

    def __init__(self, db_path: str = DATABASE_PATH) -> None:
        """Initialize database connection."""
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.init_db()

    def connect(self) -> None:
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def init_db(self) -> None:
        """Initialize database tables."""
        self.connect()
        cursor = self.conn.cursor()

        # Create users table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pin_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                telegram_id INTEGER UNIQUE,
                donation_amount TEXT NOT NULL,
                donation_link TEXT NOT NULL,
                status TEXT DEFAULT '{UserStatus.UNVERIFIED}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Create payments table
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                jalali_month INTEGER NOT NULL,
                jalali_year INTEGER NOT NULL,
                status TEXT DEFAULT '{PaymentStatus.PENDING}',
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

        # Create pending approvals table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

        self.conn.commit()
        self.seed_users()

    def seed_users(self) -> None:
        """Seed users from CSV file.

        This normalizes CSV header names (stripping whitespace) so imperfect CSV
        headers like "pin-code " still work.
        """
        cursor = self.conn.cursor()

        # Check if users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            return

        # Read CSV file
        csv_path = Path(SEED_DATA_PATH)
        if not csv_path.exists():
            logger.info("Seed CSV not found at %s, skipping seeding.", csv_path)
            return

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # normalize keys by stripping whitespace and removing BOM if present
                normalized = { (k.strip().lstrip("\ufeff") if k else ""): (v or "").strip() for k, v in row.items() }

                pin_code = normalized.get("pin-code", "")
                full_name = normalized.get("full name", "")
                amount = normalized.get("amount", "")
                donation_link = normalized.get("donation link", "")

                # Normalize pin before inserting (handles Persian digits, whitespace)
                from .utils import normalize_pin

                pin_code = normalize_pin(pin_code)

                if pin_code and full_name:
                    cursor.execute(
                        """
                        INSERT INTO users (pin_code, full_name, donation_amount, 
                                         donation_link, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            pin_code,
                            full_name,
                            amount or "0",
                            donation_link or "",
                            UserStatus.UNVERIFIED,
                        ),
                    )

        self.conn.commit()

    def get_user_by_pin(self, pin_code: str) -> Optional[dict]:
        """Get user by pin code (normalized).

        Attempts exact normalized match first, then numeric match ignoring leading
        zeros as a fallback for user convenience.
        """
        from .utils import normalize_pin

        normalized_pin = normalize_pin(pin_code)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE pin_code = ?", (normalized_pin,))
        row = cursor.fetchone()
        if row:
            return dict(row)

        # Fallback: if normalized pin is numeric, try numeric equality ignoring leading zeros
        if normalized_pin.isdigit():
            cursor.execute("SELECT * FROM users")
            for r in cursor.fetchall():
                db_pin = (r["pin_code"] or "").strip()
                if db_pin.isdigit():
                    try:
                        if int(db_pin) == int(normalized_pin):
                            return dict(r)
                    except ValueError:
                        continue

        return None

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """Get user by Telegram ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_user_telegram_id(self, user_id: int, telegram_id: int) -> None:
        """Update user's Telegram ID without changing status."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE users SET telegram_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (telegram_id, datetime.now(), user_id),
        )
        self.conn.commit()

    def logout_user_by_telegram_id(self, telegram_id: int) -> None:
        """Logout user: clear telegram_id only (don't modify status)."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE users SET telegram_id = NULL, updated_at = ?
            WHERE telegram_id = ?
            """,
            (datetime.now(), telegram_id),
        )
        self.conn.commit()

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def create_payment(
        self,
        user_id: int,
        jalali_month: int,
        jalali_year: int,
        status: str = PaymentStatus.PENDING,
    ) -> int:
        """Create a payment record."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO payments (user_id, jalali_month, jalali_year, status)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, jalali_month, jalali_year, status),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_payment_status(
        self, payment_id: int, status: str, image_path: Optional[str] = None
    ) -> None:
        """Update payment status."""
        cursor = self.conn.cursor()
        if image_path:
            cursor.execute(
                """
                UPDATE payments SET status = ?, image_path = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, image_path, datetime.now(), payment_id),
            )
        else:
            cursor.execute(
                """
                UPDATE payments SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, datetime.now(), payment_id),
            )
        self.conn.commit()

    def get_pending_payments(
        self, jalali_month: int, jalali_year: int
    ) -> list[dict]:
        """Get pending or failed payments for a month."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT p.* FROM payments p
            WHERE p.jalali_month = ? AND p.jalali_year = ?
            AND p.status IN (?, ?)
            """,
            (jalali_month, jalali_year, PaymentStatus.PENDING, PaymentStatus.FAILED),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_verified_users(self) -> list[dict]:
        """Get all users with a bound Telegram ID (contactable users)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE telegram_id IS NOT NULL"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_pending_admin_users(self) -> list[dict]:
        """Get users pending admin approval."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE status = ?", (UserStatus.PENDING_ADMIN,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def create_pending_approval(self, user_id: int) -> int:
        """Create pending approval record."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO pending_approvals (user_id) VALUES (?)", (user_id,)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_pending_approval(self, approval_id: int) -> Optional[dict]:
        """Get pending approval by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM pending_approvals WHERE id = ?", (approval_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def approve_user(self, user_id: int) -> None:
        """Approve user."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE users SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (UserStatus.VERIFIED, datetime.now(), user_id),
        )
        self.conn.commit()

    def get_monthly_summary(self, jalali_month: int, jalali_year: int) -> dict:
        """Get monthly payment summary."""
        cursor = self.conn.cursor()

        # Get all users and their payment status
        cursor.execute(
            """
            SELECT 
                u.full_name,
                u.donation_amount,
                COALESCE(p.status, ?) as payment_status
            FROM users u
            LEFT JOIN payments p ON u.id = p.user_id
                AND p.jalali_month = ? AND p.jalali_year = ?
            WHERE u.telegram_id IS NOT NULL
            ORDER BY u.full_name
            """,
            (PaymentStatus.PENDING, jalali_month, jalali_year),
        )

        rows = cursor.fetchall()
        return {
            "data": [dict(row) for row in rows],
            "month": jalali_month,
            "year": jalali_year,
        }
