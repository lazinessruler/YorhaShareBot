import os

# Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "")

# Owner & Admin
OWNER_ID = int(os.environ.get("OWNER_ID", 8587740350))  # Your Telegram ID

# Database
DB_URI = os.environ.get("DB_URI", "mongodb+srv://username:password@cluster.mongodb.net")
DB_NAME = os.environ.get("DB_NAME", "file_store_bot")

# Shortener API
SHORTENER_API = os.environ.get("SHORTENER_API", "04fed748fbf7b478eb64fea5de0ad8a426a461bc")
SHORTENER_URL = os.environ.get("SHORTENER_URL", "https://arolinks.com/api")

# Channel & Support
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/Nightfall_Hub")
SUPPORT_CONTACT = os.environ.get("SUPPORT_CONTACT", "@xFlexyy")

# Tutorial Video
TUTORIAL_URL = os.environ.get("TUTORIAL_URL", "https://t.me/your_tutorial_video_link")