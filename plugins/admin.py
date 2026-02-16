from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from config import OWNER_ID
from plugins.start import small_caps, get_random_image

@Client.on_message(filters.command("admin") & filters.private)
async def admin_panel(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if admin (only owner for now)
    if user_id != OWNER_ID:
        await message.reply_text(
            f"{small_caps('❌ Admin only command')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    total_links = await db.total_links_count()
    
    # Get shortener settings
    shortener_api = await db.get_shortener_api()
    shortener_url = await db.get_shortener_url()
    
    text = f"""
{small_caps('👑 Admin Dashboard')}

{small_caps('📊 Statistics')}:
• {small_caps('Total Links')}: <code>{total_links}</code>

{small_caps('⚙️ Shortener Settings')}:
• {small_caps('API Key')}: <code>{'✅ Set' if shortener_api else '❌ Not Set'}</code>
• {small_caps('API URL')}: <code>{'✅ Set' if shortener_url else '❌ Not Set'}</code>

{small_caps('🆔 Your ID')}: <code>{user_id}</code>
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_caps("🔗 Set Shortener"), callback_data="set_shortener"),
            InlineKeyboardButton(small_caps("📊 View Links"), callback_data="view_links")
        ],
        [InlineKeyboardButton(small_caps("❌ Close"), callback_data="close")]
    ])
    
    await client.send_photo(
        chat_id=message.chat.id,
        photo=get_random_image(),
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_callback_query()
async def admin_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message
    
    if user_id != OWNER_ID:
        await callback_query.answer(small_caps("❌ Unauthorized"), show_alert=True)
        return
    
    if data == "close":
        await message.delete()
        await callback_query.answer()
    
    elif data == "set_shortener":
        await callback_query.message.reply_text(
            f"{small_caps('🔗 Set Shortener API')}\n\n"
            f"{small_caps('Send API Key and URL in format')}:\n"
            f"<code>api_key|https://apiurl.com</code>",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "view_links":
        links = await db.get_all_links()
        if not links:
            await callback_query.answer(small_caps("📭 No links found"), show_alert=True)
            return
        
        text = f"{small_caps('📊 Stored Links')}:\n\n"
        for link in links[-10:]:  # Last 10 links
            text += f"• <code>{link['hash_id']}</code>: {link['original_url'][:50]}...\n"
        
        await callback_query.message.reply_text(
            text,
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()

@Client.on_message(filters.text & filters.private & ~filters.command(["start", "admin"]))
async def handle_admin_input(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    
    text = message.text.strip()
    
    # Check for shortener settings format
    if '|' in text:
        parts = text.split('|', 1)
        if len(parts) == 2:
            api_key = parts[0].strip()
            api_url = parts[1].strip()
            
            await db.set_shortener_api(api_key)
            await db.set_shortener_url(api_url)
            
            await message.reply_text(
                f"{small_caps('✅ Shortener settings updated')}",
                parse_mode=enums.ParseMode.HTML
            )
