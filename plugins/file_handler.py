import aiohttp
import json
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from config import OWNER_ID, SHORTENER_API, SHORTENER_URL, SUPPORT_CONTACT
from plugins.start import small_caps, get_random_start_image

@Client.on_message(filters.private & filters.document | filters.video | filters.audio | filters.photo)
async def handle_file(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is admin
    is_admin_user = await db.is_admin(user_id)
    if not is_admin_user:
        await message.reply_text(
            f"{small_caps('❌ Only admins can store files')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Get file data
    file_data = None
    if message.document:
        file_data = message.document
    elif message.video:
        file_data = message.video
    elif message.audio:
        file_data = message.audio
    elif message.photo:
        file_data = message.photo[-1]  # Get largest size
    
    if not file_data:
        return
    
    # Store file
    file_id = await db.store_file(file_data, user_id)
    
    # Create bot link
    bot_username = (await client.get_me()).username
    file_link = f"https://t.me/{bot_username}?start={file_id}"
    
    await message.reply_text(
        f"{small_caps('✅ File Stored Successfully')}!\n\n"
        f"{small_caps('Use /getlink on this file to generate short link')}\n\n"
        f"{small_caps('File ID')}: <code>{file_id}</code>",
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("getlink") & filters.private)
async def getlink_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if admin
    is_admin_user = await db.is_admin(user_id)
    if not is_admin_user:
        await message.reply_text(
            f"{small_caps('❌ Only admins can generate links')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Check if replying to a file
    if not message.reply_to_message:
        await message.reply_text(
            f"{small_caps('❌ Reply to a file with /getlink')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    reply = message.reply_to_message
    
    # Get file data
    file_data = None
    if reply.document:
        file_data = reply.document
    elif reply.video:
        file_data = reply.video
    elif reply.audio:
        file_data = reply.audio
    elif reply.photo:
        file_data = reply.photo[-1]
    else:
        await message.reply_text(
            f"{small_caps('❌ Not a supported file type')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Check if already stored
    existing = await db.get_file_by_unique_id(file_data.file_unique_id)
    if existing:
        file_id = existing['file_id']
    else:
        # Store file
        file_id = await db.store_file(file_data, user_id)
    
    # Generate short URL
    bot_username = (await client.get_me()).username
    destination_url = f"https://t.me/{bot_username}?start={file_id}"
    
    # Check if short URL already exists
    short_url = await db.get_short_url(file_id)
    
    if not short_url:
        # Generate new short URL
        short_url = await create_short_url(destination_url, file_id)
        if short_url:
            await db.save_short_url(file_id, short_url)
    
    if short_url:
        # Show the link
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(small_cps("🔗 Click Here to Download"), url=short_url)],
            [
                InlineKeyboardButton(small_cps("💎 Premium"), callback_data="premium_info"),
                InlineKeyboardButton(small_cps("📚 Tutorial"), callback_data="show_tutorial")
            ]
        ])
        
        text = f"""
{small_cps('ʏᴏᴜʀ ʟɪɴᴋ ɪs ʀᴇᴀᴅʏ')}!👇

{small_cps('ᴛᴏ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ, ᴄᴏɴᴛᴀᴄᴛ')}: {SUPPORT_CONTACT}
"""
        
        await client.send_photo(
            chat_id=message.chat.id,
            photo=get_random_start_image(),
            caption=text,
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )
    else:
        await message.reply_text(
            f"{small_cps('❌ Failed to generate short link')}",
            parse_mode=enums.ParseMode.HTML
        )

async def create_short_url(destination: str, alias: str = None) -> str:
    """Create short URL using Arolinks API"""
    try:
        api_key = await db.get_shortener_api()
        if not api_key:
            api_key = SHORTENER_API
        
        api_url = await db.get_shortener_url()
        if not api_url:
            api_url = SHORTENER_URL
        
        params = {
            'api': api_key,
            'url': destination,
            'format': 'text'
        }
        
        if alias:
            params['alias'] = alias[:20]  # Limit alias length
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=30) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Try to parse as JSON first
                    try:
                        data = json.loads(text)
                        if data.get('status') == 'success':
                            return data.get('shortenedUrl')
                    except:
                        # If not JSON, return text directly
                        if text.startswith('http'):
                            return text.strip()
        return None
    except Exception as e:
        print(f"Shortener error: {e}")
        return None