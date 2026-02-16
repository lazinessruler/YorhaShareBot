from pyrogram import Client, filters, enums
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import SUPPORT_CONTACT
from plugins.start import small_caps, get_random_image, start_command
import datetime

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
    
    elif data == "back_to_start":
        # Re-trigger start command
        await start_command(client, callback_query.message)
        await callback_query.answer()
