import re
import aiohttp
import json
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from config import SUPPORT_CONTACT, CHANNEL_URL

def small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    small = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    result = ""
    for char in text:
        if char in normal:
            idx = normal.index(char)
            result += small[idx]
        else:
            result += char
    return result

START_IMAGES = [
    "https://i.postimg.cc/Hx1qXv0f/0f22a4ab4d44a829a33797eb7d8fbdc6.jpg",
    "https://i.postimg.cc/j5YpP3Qb/22df44ff326cbce5d99344d904e993af.jpg",
    "https://i.postimg.cc/26Nsh9dg/2b8ed2a65ecec6caa3c442cd08cffd27.jpg",
    "https://i.postimg.cc/Kzh6Bprz/6274337955fefbe4c95d4712714597e4.jpg",
    "https://i.postimg.cc/SsLwrLDN/9a8fe855f0dc641cf81aae32d9f0e9bb.jpg",
    "https://i.postimg.cc/vB7pz73Z/a08029e31cd662dcb778a917b09deee4.jpg",
    "https://i.postimg.cc/ydhwPhvz/a85d30361837800fd31935ec137863bf.jpg",
    "https://i.postimg.cc/LsPdqFPW/b6e808ff4ded204ba2abadedaeeef2b2.jpg",
    "https://i.postimg.cc/vBwJf2Ly/bd7b083aebb810f4ffba2d60ee98053a.jpg",
    "https://i.postimg.cc/W3mQnmXc/cfbf4a2ce731632aa88dd87456844586.jpg",
    "https://i.postimg.cc/85dqHdtS/f4895703153ffd7f73fa8024eada8287.jpg"
]

def get_random_image():
    import random
    return random.choice(START_IMAGES)

async def create_short_url(destination: str, alias: str = None) -> str:
    """Create short URL using Arolinks API"""
    try:
        api_key = await db.get_shortener_api()
        api_url = await db.get_shortener_url()
        
        if not api_key or not api_url:
            return None
        
        params = {
            'api': api_key,
            'url': destination,
            'format': 'text'
        }
        
        if alias:
            params['alias'] = alias[:20]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=30) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # Try JSON first
                    try:
                        data = json.loads(text)
                        if data.get('status') == 'success':
                            return data.get('shortenedUrl')
                    except:
                        # Return plain text URL
                        if text.startswith('http'):
                            return text.strip()
        return None
    except Exception as e:
        print(f"Shortener error: {e}")
        return None

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await db.add_user(user_id, username, first_name)
    
    # Check if it's a deep link (hash access)
    if len(message.command) > 1:
        hash_id = message.command[1]
        await handle_hash_access(client, message, hash_id)
        return
    
    # Normal start message
    welcome_text = f"""
{small_caps('Hɪ Tʜᴇʀᴇ...')} {message.from_user.mention} !!! 💥

{small_caps('I ᴀᴍ ᴀ ʟɪɴᴋ sᴛᴏʀᴇ ʙᴏᴛ')}
{small_caps('Sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ʟɪɴᴋ ᴀɴᴅ ɪ ᴡɪʟʟ ᴄʀᴇᴀᴛᴇ ᴀ sʜᴏʀᴛ ʟɪɴᴋ')}

{small_caps('Pᴏᴡᴇʀᴇᴅ Bʏ')}: @Nightfall_Hub
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("📢 Channel"), url=CHANNEL_URL),
            InlineKeyboardButton(small_caps("💎 Premium"), url=f"https://t.me/{SUPPORT_CONTACT[1:]}")
        ]
    ])
    
    await client.send_photo(
        chat_id=message.chat.id,
        photo=get_random_image(),
        caption=welcome_text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

async def handle_hash_access(client: Client, message: Message, hash_id: str):
    """Handle access via hash (user clicked short link)"""
    # Get original URL from database
    original_url = await db.get_original_url(hash_id)
    
    if not original_url:
        await message.reply_text(
            f"{small_cps('❌ Invalid or expired link')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Send the original link to user
    await message.reply_text(
        f"{small_cps('ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ')}:\n\n{original_url}",
        parse_mode=enums.ParseMode.HTML
    )
