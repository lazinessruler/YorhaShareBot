import motor.motor_asyncio
import datetime
import random
import string
from config import DB_URI, DB_NAME, OWNER_ID
from logger import LOGGER

logger = LOGGER(__name__)

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files = self.db.files
        self.users = self.db.users
        self.admins = self.db.admins
        self.settings = self.db.settings
        self.shortener = self.db.shortener
    
    # ==================== USER FUNCTIONS ====================
    
    async def add_user(self, user_id, username=None, first_name=None):
        user = await self.users.find_one({'user_id': user_id})
        if not user:
            await self.users.insert_one({
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'joined_date': datetime.datetime.now(),
                'is_premium': False,
                'premium_expiry': None,
                'total_used': 0
            })
            logger.info(f"✅ New user added: {user_id}")
    
    async def get_user(self, user_id):
        return await self.users.find_one({'user_id': user_id})
    
    async def get_all_users(self):
        cursor = self.users.find({})
        return await cursor.to_list(length=None)
    
    async def total_users_count(self):
        return await self.users.count_documents({})
    
    # ==================== PREMIUM FUNCTIONS ====================
    
    async def add_premium(self, user_id, days):
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        await self.users.update_one(
            {'user_id': user_id},
            {'$set': {'is_premium': True, 'premium_expiry': expiry}}
        )
        logger.info(f"💎 Premium added to {user_id} for {days} days")
    
    async def remove_premium(self, user_id):
        await self.users.update_one(
            {'user_id': user_id},
            {'$set': {'is_premium': False, 'premium_expiry': None}}
        )
        logger.info(f"💎 Premium removed from {user_id}")
    
    async def check_premium(self, user_id):
        user = await self.users.find_one({'user_id': user_id})
        if not user or not user.get('is_premium'):
            return False
        expiry = user.get('premium_expiry')
        if expiry and expiry > datetime.datetime.now():
            return True
        # Auto-remove expired
        await self.remove_premium(user_id)
        return False
    
    # ==================== ADMIN FUNCTIONS ====================
    
    async def add_admin(self, user_id):
        await self.admins.update_one(
            {'user_id': user_id},
            {'$set': {'user_id': user_id}},
            upsert=True
        )
        logger.info(f"👑 Admin added: {user_id}")
    
    async def remove_admin(self, user_id):
        if user_id == OWNER_ID:
            return False
        await self.admins.delete_one({'user_id': user_id})
        logger.info(f"👑 Admin removed: {user_id}")
        return True
    
    async def is_admin(self, user_id):
        if user_id == OWNER_ID:
            return True
        admin = await self.admins.find_one({'user_id': user_id})
        return bool(admin)
    
    async def get_all_admins(self):
        cursor = self.admins.find({})
        admins = await cursor.to_list(length=None)
        return [a['user_id'] for a in admins]
    
    # ==================== FILE STORE FUNCTIONS ====================
    
    def generate_file_id(self):
        """Generate unique file ID"""
        chars = string.ascii_letters + string.digits
        return 'get-' + ''.join(random.choices(chars, k=12))
    
    async def store_file(self, file_data, user_id):
        """Store file and return file_id"""
        file_id = self.generate_file_id()
        
        # Check if already exists
        existing = await self.files.find_one({'file_unique_id': file_data.file_unique_id})
        if existing:
            return existing['file_id']
        
        await self.files.insert_one({
            'file_id': file_id,
            'message_id': file_data.message_id,
            'chat_id': file_data.chat.id,
            'file_unique_id': file_data.file_unique_id,
            'file_type': file_data.__class__.__name__.lower(),
            'caption': file_data.caption,
            'stored_by': user_id,
            'stored_at': datetime.datetime.now(),
            'short_url': None,
            'access_count': 0
        })
        
        logger.info(f"📁 File stored: {file_id}")
        return file_id
    
    async def get_file(self, file_id):
        """Get file by file_id"""
        return await self.files.find_one({'file_id': file_id})
    
    async def get_file_by_unique_id(self, unique_id):
        """Get file by unique_id"""
        return await self.files.find_one({'file_unique_id': unique_id})
    
    async def increment_access(self, file_id):
        """Increment access count"""
        await self.files.update_one(
            {'file_id': file_id},
            {'$inc': {'access_count': 1}}
        )
    
    async def get_all_files(self):
        cursor = self.files.find({})
        return await cursor.to_list(length=None)
    
    async def total_files_count(self):
        return await self.files.count_documents({})
    
    # ==================== SHORTENER FUNCTIONS ====================
    
    async def save_short_url(self, file_id, short_url):
        """Save short URL for file"""
        await self.files.update_one(
            {'file_id': file_id},
            {'$set': {'short_url': short_url}}
        )
    
    async def get_short_url(self, file_id):
        """Get short URL for file"""
        file = await self.files.find_one({'file_id': file_id})
        return file.get('short_url') if file else None
    
    async def refresh_all_short_urls(self):
        """Clear all short URLs for regeneration"""
        await self.files.update_many(
            {},
            {'$set': {'short_url': None}}
        )
        logger.info("🔄 All short URLs cleared for refresh")
    
    # ==================== SETTINGS FUNCTIONS ====================
    
    async def set_tutorial(self, url):
        await self.settings.update_one(
            {'key': 'tutorial'},
            {'$set': {'value': url}},
            upsert=True
        )
    
    async def get_tutorial(self):
        setting = await self.settings.find_one({'key': 'tutorial'})
        return setting.get('value') if setting else None
    
    async def set_shortener_api(self, api_key):
        await self.settings.update_one(
            {'key': 'shortener_api'},
            {'$set': {'value': api_key}},
            upsert=True
        )
    
    async def get_shortener_api(self):
        setting = await self.settings.find_one({'key': 'shortener_api'})
        return setting.get('value') if setting else None
    
    async def set_shortener_url(self, url):
        await self.settings.update_one(
            {'key': 'shortener_url'},
            {'$set': {'value': url}},
            upsert=True
        )
    
    async def get_shortener_url(self):
        setting = await self.settings.find_one({'key': 'shortener_url'})
        return setting.get('value') if setting else None

# Initialize database
db = Database(DB_URI, DB_NAME)
