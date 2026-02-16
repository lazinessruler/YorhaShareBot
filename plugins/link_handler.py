import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import SUPPORT_CONTACT
from plugins.start import small_caps, get_random_image, create_short_url

# Telegram link pattern
TELEGRAM_LINK_PATTERN = r'https?://t\.me/\S+'

@Client.on_message(filters.text & filters.private & ~filters.command(["start"]))
async def handle_link(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check if message contains Telegram link
    if not re.search(TELEGRAM_LINK_PATTERN, text):
        return
    
    # Extract the link
    link_match = re.search(TELEGRAM_LINK_PATTERN, text)
    if not link_match:
        return
    
    original_link = link_match.group(0)
    
    # Store the link and get hash
    hash_id = await db.store_link(original_link, user_id)
    
    # Increment user's link count
    await db.increment_user_links(user_id)
    
    # Create bot link
    bot_username = (await client.get_me()).username
    bot_link = f"https://t.me/{bot_username}?start={hash_id}"
    
    # Check if short URL already exists
    short_url = await db.get_short_url(hash_id)
    
    if not short_url:
        # Generate short URL
        await message.reply_text(
            f"{small_cps('⏳ Generating short link...')}",
            parse_mode=enums.ParseMode.HTML
        )
        
        short_url = await create_short_url(bot_link, hash_id)
        if short_url:
            await db.save_short_url(hash_id, short_url)
    
    if short_url:
        # Send the short link to user
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(small_cps("🔗 Click Here"), url=short_url)],
            [InlineKeyboardButton(small_cps("💎 Premium"), url=f"https://t.me/{SUPPORT_CONTACT[1:]}")]
        ])
        
        text = f"""
{small_cps('ʏᴏᴜʀ ʟɪɴᴋ ɪs ʀᴇᴀᴅʏ')}! 👇

{small_cps('ᴛᴏ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ, ᴄᴏɴᴛᴀᴄᴛ')}: {SUPPORT_CONTACT}
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
        await message.reply_text(
            f"{small_cps('ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ')}:\n\n{bot_link}",
            parse_mode=enums.ParseMode.HTML
        )
