#!/usr/bin/env python3
# File Store Bot
# Developed by: Flexyy 🔥
# Telegram: @xFlexyy | @DragonByte_Network

import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN
from database.db import db

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create plugins list
plugins = dict(
    root="plugins"
)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="file_store_bot",
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
        await db.add_user(me.id, me.username, me.first_name)
        
        # Add owner as admin
        from config import OWNER_ID
        await db.add_admin(OWNER_ID)
        
        logger.info(f"👑 Owner ID: {OWNER_ID}")
    
    async def stop(self):
        await super().stop()
        logger.info("❌ Bot stopped")

if __name__ == "__main__":
    Bot().run()