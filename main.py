#!/usr/bin/env python3
# Link Store Bot
# Developed by: Flexyy 🔥
# Telegram: @xFlexyy

import os
import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    async def stop(self):
        await super().stop()
        logger.info("❌ Bot stopped")

if __name__ == "__main__":
    Bot().run()
