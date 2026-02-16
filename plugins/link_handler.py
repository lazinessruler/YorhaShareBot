import re
import time
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import SUPPORT_CONTACT
from plugins.start import small_caps, get_random_image, create_short_url

# Better pattern to match all Telegram links
TELEGRAM_LINK_PATTERN = r'(https?://)?(www\.)?(t\.me|telegram\.me|telegram\.dog)/[a-zA-Z0-9_/+\-?=]+'

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "admin"]))
async def handle_link(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    print(f"Received message: {text}")  # Debug log
    
    # Check if message contains Telegram link
    link_match = re.search(TELEGRAM_LINK_PATTERN, text)
    if not link_match:
        print("No Telegram link found")  # Debug log
        return  # Ignore messages without links
    
    # Extract the link
    original_link = link_match.group(0)
    print(f"Found link: {original_link}")  # Debug log
    
    # Send typing action to show bot is working
    await client.send_chat_action(message.chat.id, "typing")
    
    # Store the link and get hash
    hash_id = await db.store_link(original_link, user_id)
    
    if not hash_id:
        await message.reply_text(
            f"{small_caps('❌ Failed to store link')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Increment user's link count
    await db.increment_user_links(user_id)
    
    # Create bot link
    bot_username = (await client.get_me()).username
    bot_link = f"https://t.me/{bot_username}?start={hash_id}"
    
    # Check if short URL already exists
    short_url = await db.get_short_url(hash_id)
    
    if not short_url:
        # Generate short URL
        processing_msg = await message.reply_text(
            f"{small_caps('⏳ Generating short link...')}",
            parse_mode=enums.ParseMode.HTML
        )
        
        short_url = await create_short_url(bot_link, hash_id)
        await processing_msg.delete()
        
        if short_url:
            await db.save_short_url(hash_id, short_url)
    
    if short_url:
        # Send the short link to user
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(small_caps("🔗 Click Here"), url=short_url)],
            [
                InlineKeyboardButton(small_caps("💎 Premium"), url=f"https://t.me/{SUPPORT_CONTACT[1:]}"),
                InlineKeyboardButton(small_caps("📢 Channel"), url="https://t.me/DragonByte_Network")
            ]
        ])
        
        text = f"""
{small_caps('ʏᴏᴜʀ ʟɪɴᴋ ɪs ʀᴇᴀᴅʏ')}! 👇

{small_caps('ᴛᴏ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ, ᴄᴏɴᴛᴀᴄᴛ')}: {SUPPORT_CONTACT}
"""
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=get_random_image(),
            caption=text,
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        # Fallback: send bot link directly
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(small_caps("🔗 Open Link"), url=bot_link)],
            [InlineKeyboardButton(small_caps("💎 Premium"), url=f"https://t.me/{SUPPORT_CONTACT[1:]}")]
        ])
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=get_random_image(),
            caption=f"{small_caps('ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ')}:",
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )
