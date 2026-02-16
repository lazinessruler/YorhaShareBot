import random
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from config import OWNER_ID, CHANNEL_URL, SUPPORT_CONTACT

# ==================== PREMIUM IMAGES ====================
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

def get_random_start_image():
    return random.choice(START_IMAGES)

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

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Add user to database
    await db.add_user(user_id, username, first_name)
    
    # Check if it's a deep link (file access)
    if len(message.command) > 1:
        file_id = message.command[1]
        await handle_file_access(client, message, file_id)
        return
    
    # Normal start message
    welcome_text = f"""
{small_caps('Hɪ Tʜᴇʀᴇ...')} ⁭⁬⁭- ⁭⁬⁭⁬⁭⁬⁭⁬⁭⁬⁭⁬⁭⁬⁭⁬⁭ {message.from_user.mention} !!! 💥

{small_caps('I ᴀᴍ ᴀ ᴘʀᴇᴍɪᴜᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ')}.
{small_caps('I ᴄᴀɴ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋs ᴅɪʀᴇᴄᴛʟʏ ᴡɪᴛʜ ɴᴏ ᴘʀᴏʙʟᴇᴍs')}

{small_caps('Pᴏᴡᴇʀᴇᴅ Bʏ')}: @Nightfall_Hub
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("📢 Channel"), url=CHANNEL_URL),
            InlineKeyboardButton(small_caps("💎 Premium"), callback_data="premium_info")
        ],
        [
            InlineKeyboardButton(small_caps("📚 Tutorial"), callback_data="show_tutorial"),
            InlineKeyboardButton(small_caps("👤 My Profile"), callback_data="my_profile")
        ]
    ])
    
    await client.send_photo(
        chat_id=message.chat.id,
        photo=get_random_start_image(),
        caption=welcome_text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

async def handle_file_access(client: Client, message: Message, file_id: str):
    """Handle file access via deep link"""
    user_id = message.from_user.id
    
    # Get file from database
    file_data = await db.get_file(file_id)
    if not file_data:
        await message.reply_text(
            f"{small_caps('❌ Invalid or expired link')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Increment access count
    await db.increment_access(file_id)
    
    # Check if short URL exists
    short_url = await db.get_short_url(file_id)
    
    if not short_url:
        # No short URL yet - generate one
        await message.reply_text(
            f"{small_caps('⏳ Generating your link...')}",
            parse_mode=enums.ParseMode.HTML
        )
        # This will be handled by callback
        return
    
    # Show short URL with buttons
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(small_caps("🔗 Click Here to Download"), url=short_url)],
        [
            InlineKeyboardButton(small_caps("💎 Premium"), callback_data="premium_info"),
            InlineKeyboardButton(small_caps("📚 Tutorial"), callback_data="show_tutorial")
        ]
    ])
    
    text = f"""
{small_caps('ʏᴏᴜʀ ʟɪɴᴋ ɪs ʀᴇᴀᴅʏ')}!👇

{small_caps('ᴛᴏ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ, ᴄᴏɴᴛᴀᴄᴛ')}: {SUPPORT_CONTACT}
"""
    
    await client.send_photo(
        chat_id=message.chat.id,
        photo=get_random_start_image(),
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )