# Aharar Charity Bot

A Telegram bot for managing charitable donations with Persian language support and Jalali calendar integration.

## Features

- **User Authentication**: PIN-based user verification using seed data from CSV
- **Donation Management**: Track and manage monthly donations
- **Payment Tracking**: Monitor payment status (pending, approved, failed)
- **Automatic Notifications**:
  - 3rd of each Jalali month: Donation payment reminders
  - 7th of each Jalali month: Follow-up reminders for unpaid donations
  - 10th of each Jalali month: Monthly reports in Excel and PDF format
- **Admin Approval**: Payment image verification workflow
- **Jalali Calendar Support**: Full Persian calendar integration with Asia/Tehran timezone
- **Type Hints**: Full type hinting throughout the codebase using Python 3.11+
- **Data Validation**: Pydantic models for all data structures

## Project Structure

```
aharar-bot/
├── main.py                 # Main bot application
├── config.py              # Configuration and constants
├── database.py            # SQLite database management
├── models.py              # Pydantic data models
├── handlers.py            # User interaction handlers
├── scheduler.py           # Scheduled tasks for notifications
├── utils.py               # Utility functions (Jalali calendar, formatting)
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container setup
├── docker-compose.yml    # Docker Compose configuration
├── .env.example          # Environment variables template
├── data/                 # Seed data directory
│   └── seed_data.csv     # User data with PIN codes
├── messages.md           # Message templates
└── payments/             # Uploaded payment images
```

## Technology Stack

- **Python 3.11+**: Core language with type hints
- **python-telegram-bot 20.7**: Telegram bot framework
- **SQLite3**: Lightweight database
- **Pydantic 2.5**: Data validation and serialization
- **pytz**: Timezone management
- **openpyxl**: Excel report generation
- **reportlab**: PDF report generation
- **Docker & Docker Compose**: Containerization

## Setup and Installation

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ and pip

### Option 1: Using Docker (Recommended)

1. Clone the repository and navigate to the project directory:
```bash
cd aharar-bot
```

2. Create `.env` file from template:
```bash
cp .env.example .env
```

3. Edit `.env` and add your bot token and admin chat ID:
```bash
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_admin_chat_id
```

4. Start the bot with Docker Compose:
```bash
docker-compose up -d
```

5. Access SQLite web viewer at `http://localhost:8080`

### Option 2: Local Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` with your bot token and admin chat ID

5. Run the bot:
```bash
python main.py
```

## Bot Commands

### User Commands

- `/start` - Start the bot and verify with PIN code
- `/کارت` - Show donation card number
- `/لینک` - Get donation payment link
- `/مبلغ` - Show your donation amount
- `/آپلود` - Upload payment receipt image
- `/سابقه` - View payment history
- `/گزارش` - Get latest charity report

### Admin Features

- Receive payment notifications and images
- Approve or deny payments with inline buttons
- Receive monthly reports (Excel and PDF)

## User Flow

1. **Verification**: User starts bot → Enters PIN code → Confirms identity
2. **Main Menu**: Access donation information, upload payments, view history
3. **Payment Upload**: User uploads payment receipt → Admin reviews → User notified of approval/denial
4. **Automated Notifications**:
   - Day 3: Monthly donation reminders sent to all users
   - Day 7: Follow-up reminders for unpaid donations
   - Day 10: Monthly summary reports sent to admin

## Database Schema

### Users Table
- `id`: Unique identifier
- `pin_code`: User's PIN for verification
- `full_name`: User's full name
- `telegram_id`: Telegram user ID (added after verification)
- `donation_amount`: Monthly donation amount
- `donation_link`: Payment link
- `status`: Account status (unverified, verified, pending_admin)
- `created_at`, `updated_at`: Timestamps

### Payments Table
- `id`: Unique identifier
- `user_id`: Reference to user
- `jalali_month`: Jalali calendar month
- `jalali_year`: Jalali calendar year
- `status`: Payment status (pending, approved, failed)
- `image_path`: Path to payment receipt image
- `created_at`, `updated_at`: Timestamps

### Pending Approvals Table
- `id`: Unique identifier
- `user_id`: Reference to user
- `status`: Approval status
- `created_at`: Timestamp

## Configuration

Edit `config.py` to customize:
- Bot behavior
- Notification timing
- Jalali calendar month names
- Payment status constants
- User status constants

## Environment Variables

Create a `.env` file with:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here
DATABASE_PATH=aharar_bot.db
SEED_DATA_PATH=./data/seed_data.csv
TIMEZONE=Asia/Tehran
```

## Development

### Adding New Features

1. Add handlers in `handlers.py`
2. Add database methods in `database.py`
3. Add data models in `models.py`
4. Update main.py to register handlers
5. Use type hints throughout

### Database Management

- Access SQLite web viewer at `http://localhost:8080` (when using Docker)
- Seed data is automatically imported from `data/seed_data.csv` on first run

### Reports

- Excel and PDF reports are generated automatically on the 10th of each month
- Reports include all users and their payment status

## Troubleshooting

### Bot not responding
- Check `BOT_TOKEN` in `.env` is correct
- Verify bot has proper permissions in Telegram
- Check logs: `docker logs aharar_bot`

### Users not receiving notifications
- Verify `TIMEZONE` is set to `Asia/Tehran`
- Check admin user IDs are saved in database
- Review `scheduler.py` notification settings

### Payment uploads not working
- Ensure `/payments` directory exists
- Check file permissions in Docker volume
- Verify ADMIN_CHAT_ID is correct

## License

This project is created for Aharar Charity.

## Support

For technical issues or feature requests, contact the development team.
