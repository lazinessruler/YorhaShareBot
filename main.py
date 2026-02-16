#!/usr/bin/env python3
# Link Store Bot
# Developed by: Flexyy 🔥
# Telegram: @xFlexyy | @DragonByte_Network

import os
import logging
import threading
from flask import Flask
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app for Render port binding
app = Flask(__name__)

@app.route('/')
def home():
    return "Link Store Bot is running! 🚀"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Run Flask app to bind to PORT"""
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Pyrogram plugins
plugins = dict(root="plugins")

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="link_store_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=plugins,
            workers=50
        )
    
    async def start(self):
        await super().start()
        me = await self.get_me()
        logger.info(f"✅ Bot started: @{me.username}")
        
        # Initialize database
        from database.db import db
        await db.add_user(me.id, me.username, me.first_name)
    
    async def stop(self):
        await super().stop()
        logger.info("❌ Bot stopped")

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask server started for port binding")
    
    # Start bot
    Bot().run()
