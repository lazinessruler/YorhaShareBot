from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from config import OWNER_ID, SUPPORT_CONTACT
from plugins.start import small_caps, get_random_start_image
import datetime

@Client.on_message(filters.command("admin") & filters.private)
async def admin_panel(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if admin
    is_admin_user = await db.is_admin(user_id)
    if not is_admin_user:
        await message.reply_text(
            f"{small_cps('❌ Admin only command')}",
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    # Get stats
    total_users = await db.total_users_count()
    total_files = await db.total_files_count()
    
    # Get shortener settings
    shortener_api = await db.get_shortener_api()
    shortener_url = await db.get_shortener_url()
    tutorial = await db.get_tutorial()
    
    text = f"""
{small_cps('👑 Admin Dashboard')}

{small_cps('📊 Statistics')}:
• {small_cps('Total Users')}: <code>{total_users}</code>
• {small_cps('Total Files')}: <code>{total_files}</code>

{small_cps('⚙️ Settings')}:
• {small_cps('Shortener API')}: <code>{'✅ Set' if shortener_api else '❌ Not Set'}</code>
• {small_cps('Shortener URL')}: <code>{'✅ Set' if shortener_url else '❌ Not Set'}</code>
• {small_cps('Tutorial')}: <code>{'✅ Set' if tutorial else '❌ Not Set'}</code>

{small_cps('🆔 Your ID')}: <code>{user_id}</code>
{small_cps('👑 Owner ID')}: <code>{OWNER_ID}</code>
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(small_cps("➕ Add Admin"), callback_data="admin_add"),
            InlineKeyboardButton(small_cps("➖ Remove Admin"), callback_data="admin_remove")
        ],
        [
            InlineKeyboardButton(small_cps("💎 Add Premium"), callback_data="admin_add_premium"),
            InlineKeyboardButton(small_cps("💎 Remove Premium"), callback_data="admin_remove_premium")
        ],
        [
            InlineKeyboardButton(small_cps("🔗 Set Shortener"), callback_data="admin_set_shortener"),
            InlineKeyboardButton(small_cps("📚 Set Tutorial"), callback_data="admin_set_tutorial")
        ],
        [
            InlineKeyboardButton(small_cps("🔄 Refresh All Links"), callback_data="admin_refresh"),
            InlineKeyboardButton(small_cps("📊 Broadcast"), callback_data="admin_broadcast")
        ],
        [InlineKeyboardButton(small_cps("❌ Close"), callback_data="close")]
    ])
    
    await client.send_photo(
        chat_id=message.chat.id,
        photo=get_random_start_image(),
        caption=text,
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_callback_query()
async def admin_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message
    
    # Check admin for all except close
    if data != "close":
        is_admin_user = await db.is_admin(user_id)
        if not is_admin_user:
            await callback_query.answer(small_cps("❌ Unauthorized"), show_alert=True)
            return
    
    if data == "close":
        await message.delete()
        await callback_query.answer()
        return
    
    elif data == "admin_add":
        await callback_query.message.reply_text(
            f"{small_cps('➕ Add Admin')}\n\n"
            f"{small_cps('Send user ID to add as admin')}:",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_remove":
        admins = await db.get_all_admins()
        if not admins:
            await callback_query.answer(small_cps("❌ No admins"), show_alert=True)
            return
        
        admin_list = "\n".join([f"• <code>{a}</code>" for a in admins if a != OWNER_ID])
        await callback_query.message.reply_text(
            f"{small_cps('➖ Remove Admin')}\n\n"
            f"{small_cps('Current Admins')}:\n{admin_list}\n\n"
            f"{small_cps('Send user ID to remove')}:",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_add_premium":
        await callback_query.message.reply_text(
            f"{small_cps('💎 Add Premium')}\n\n"
            f"{small_cps('Send user ID and days')}:\n"
            f"{small_cps('Example')}: <code>123456789 30</code>",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_remove_premium":
        await callback_query.message.reply_text(
            f"{small_cps('💎 Remove Premium')}\n\n"
            f"{small_cps('Send user ID to remove premium')}:",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_set_shortener":
        current_api = await db.get_shortener_api()
        current_url = await db.get_shortener_url()
        
        text = f"""
{small_cps('🔗 Set Shortener API')}

{small_cps('Current API')}: <code>{current_api or 'Not Set'}</code>
{small_cps('Current URL')}: <code>{current_url or 'Not Set'}</code>

{small_cps('Send new API key and URL')}:
{small_cps('Format')}: <code>api_key|https://apiurl.com</code>
"""
        await callback_query.message.reply_text(
            text,
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_set_tutorial":
        current = await db.get_tutorial()
        await callback_query.message.reply_text(
            f"{small_cps('📚 Set Tutorial Link')}\n\n"
            f"{small_cps('Current')}: <code>{current or 'Not Set'}</code>\n\n"
            f"{small_cps('Send new tutorial link')}:",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_refresh":
        # Confirm refresh
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(small_cps("✅ Yes"), callback_data="confirm_refresh"),
                InlineKeyboardButton(small_cps("❌ No"), callback_data="close")
            ]
        ])
        await callback_query.message.edit_caption(
            caption=f"{small_cps('🔄 Are you sure you want to refresh all short links?')}\n\n{small_cps('This will regenerate all short URLs')}.",
            reply_markup=buttons,
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "confirm_refresh":
        await db.refresh_all_short_urls()
        await callback_query.message.edit_caption(
            caption=f"{small_cps('✅ All short links cleared for refresh')}\n\n{small_cps('New links will be generated when accessed')}.",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "admin_broadcast":
        await callback_query.message.reply_text(
            f"{small_cps('📢 Broadcast Message')}\n\n"
            f"{small_cps('Send the message to broadcast to all users')}:",
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()