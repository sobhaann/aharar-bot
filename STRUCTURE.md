# Aharar Charity Bot - Clean Project Structure

## Project Organization

Your project has been reorganized into a clean, professional structure:

```
aharar-bot/
├── aharar_bot/                 # Main package
│   ├── __init__.py             # Package initialization
│   ├── config.py               # Configuration & constants
│   ├── database.py             # Database management
│   ├── handlers.py             # User interaction handlers
│   ├── models.py               # Pydantic data models
│   ├── scheduler.py            # Scheduled tasks
│   └── utils.py                # Utility functions
├── docker/                     # Docker configuration
│   └── Dockerfile              # Container image definition
├── scripts/                    # Utility scripts
│   ├── setup.sh                # Local setup script
│   └── run.sh                  # Quick start script
├── .github/
│   └── workflows/
│       └── run-bot.yml         # GitHub Actions workflow
├── data/
│   └── seed_data.csv           # User seed data
├── main.py                     # Bot entry point
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── README.md                   # Project documentation
├── IMPLEMENTATION.md           # Implementation details
└── ...                         # Configuration files
```

## Key Improvements

### 1. **Modular Package Structure**
- All bot code organized under `aharar_bot/` package
- Clean separation of concerns
- Easy to import and test modules
- Professional Python package layout

### 2. **Organized Directories**
- `docker/` - All Docker-related files
- `scripts/` - Utility scripts for setup and running
- `.github/workflows/` - CI/CD automation
- `data/` - Seed data and static files

### 3. **Clean Root Directory**
- Only necessary files at root level
- Removed duplicate files (old config.py, database.py, etc. now in aharar_bot/)
- Docker and Docker Compose at root for easy access
- Clear entry point with main.py

### 4. **GitHub Actions Workflow**
- `.github/workflows/run-bot.yml` automatically runs the bot
- Environment variables set from GitHub Secrets
- Daily scheduled runs possible
- Supports CI/CD pipeline

## Updated Imports

All imports have been updated to use the new package structure:

```python
# Old
from config import BOT_TOKEN
from handlers import start

# New
from aharar_bot.config import BOT_TOKEN
from aharar_bot.handlers import start
```

## Running the Bot

### Using Docker Compose (Recommended)
```bash
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

### Local Development
```bash
bash scripts/setup.sh
nano .env
python main.py
```

## File Mapping

**Old Structure → New Structure:**
- `config.py` → `aharar_bot/config.py`
- `database.py` → `aharar_bot/database.py`
- `handlers.py` → `aharar_bot/handlers.py`
- `models.py` → `aharar_bot/models.py`
- `scheduler.py` → `aharar_bot/scheduler.py`
- `utils.py` → `aharar_bot/utils.py`
- `Dockerfile` → `docker/Dockerfile`
- `setup.sh` → `scripts/setup.sh`
- `run.sh` → `scripts/run.sh`

**Old Files at Root (can be deleted):**
- config.py
- database.py
- handlers.py
- models.py
- scheduler.py
- utils.py
- Dockerfile

## GitHub Actions Setup

To enable the GitHub Actions workflow:

1. Go to your GitHub repository settings
2. Add these secrets:
   - `BOT_TOKEN` - Your Telegram bot token
   - `ADMIN_CHAT_ID` - Admin chat ID for notifications

The workflow will automatically run:
- On push to main/master/develop branches
- On pull requests
- Daily at 9:00 UTC

## Benefits of This Structure

✅ **Professional Layout** - Follows Python packaging standards
✅ **Scalability** - Easy to add new modules
✅ **Maintainability** - Clear organization and separation
✅ **CI/CD Ready** - GitHub Actions configured
✅ **Docker Ready** - Organized docker files
✅ **Testing Friendly** - Easy to write tests for each module
✅ **Deployment Ready** - Production-ready structure
