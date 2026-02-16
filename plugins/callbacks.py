from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import SUPPORT_CONTACT, TUTORIAL_URL
from plugins.start import small_caps, get_random_start_image

@Client.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message
    
    if data == "premium_info":
        text = f"""
{small_caps('💎 Premium Benefits')}

✅ {small_caps('No ads')}
✅ {small_caps('Faster downloads')}
✅ {small_caps('Priority support')}
✅ {small_caps('Higher limits')}

{small_caps('To purchase premium, contact')}: {SUPPORT_CONTACT}
"""
        await message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(small_caps("⬅️ Back"), callback_data="back_to_start")]
            ]),
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "show_tutorial":
        tutorial = await db.get_tutorial()
        if not tutorial:
            tutorial = TUTORIAL_URL
        
        text = f"""
{small_caps('📚 Tutorial')}

{small_caps('Watch the video below to learn how to use this bot')}:

{tutorial}
"""
        await message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(small_caps("▶️ Watch Tutorial"), url=tutorial)],
                [InlineKeyboardButton(small_caps("⬅️ Back"), callback_data="back_to_start")]
            ]),
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "my_profile":
        user = await db.get_user(user_id)
        is_premium = await db.check_premium(user_id)
        
        premium_status = small_caps("✅ Active") if is_premium else small_caps("❌ Not Active")
        joined = user.get('joined_date', 'Unknown')
        if isinstance(joined, datetime.datetime):
            joined = joined.strftime('%Y-%m-%d')
        
        text = f"""
{small_caps('👤 Your Profile')}

{small_caps('User ID')}: <code>{user_id}</code>
{small_caps('Premium')}: {premium_status}
{small_caps('Joined')}: {joined}
"""
        await message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(small_caps("⬅️ Back"), callback_data="back_to_start")]
            ]),
            parse_mode=enums.ParseMode.HTML
        )
        await callback_query.answer()
    
    elif data == "back_to_start":
        from plugins.start import start_command
        await start_command(client, callback_query.message)
        await callback_query.answer()