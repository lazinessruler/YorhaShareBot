import motor.motor_asyncio
import datetime
import random
import string
import asyncio
from config import DB_URI, DB_NAME, OWNER_ID

# Try to import logger, but don't fail if not available
try:
    from logger import LOGGER
    logger = LOGGER(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.files = self.db.files
        self.users = self.db.users
        self.admins = self.db.admins
        self.settings = self.db.settings
    
    # ==================== USER FUNCTIONS ====================
    
    async def add_user(self, user_id, username=None, first_name=None):
        try:
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
        except Exception as e:
            logger.error(f"Error adding user: {e}")
    
    async def get_user(self, user_id):
        try:
            return await self.users.find_one({'user_id': user_id})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def get_all_users(self):
        try:
            cursor = self.users.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def total_users_count(self):
        try:
            return await self.users.count_documents({})
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    # ==================== PREMIUM FUNCTIONS ====================
    
    async def add_premium(self, user_id, days):
        try:
            expiry = datetime.datetime.now() + datetime.timedelta(days=days)
            await self.users.update_one(
                {'user_id': user_id},
                {'$set': {'is_premium': True, 'premium_expiry': expiry}}
            )
            logger.info(f"💎 Premium added to {user_id} for {days} days")
        except Exception as e:
            logger.error(f"Error adding premium: {e}")
    
    async def remove_premium(self, user_id):
        try:
            await self.users.update_one(
                {'user_id': user_id},
                {'$set': {'is_premium': False, 'premium_expiry': None}}
            )
            logger.info(f"💎 Premium removed from {user_id}")
        except Exception as e:
            logger.error(f"Error removing premium: {e}")
    
    async def check_premium(self, user_id):
        try:
            user = await self.users.find_one({'user_id': user_id})
            if not user or not user.get('is_premium'):
                return False
            expiry = user.get('premium_expiry')
            if expiry and expiry > datetime.datetime.now():
                return True
            # Auto-remove expired
            if expiry and expiry <= datetime.datetime.now():
                await self.remove_premium(user_id)
            return False
        except Exception as e:
            logger.error(f"Error checking premium: {e}")
            return False
    
    # ==================== ADMIN FUNCTIONS ====================
    
    async def add_admin(self, user_id):
        try:
            await self.admins.update_one(
                {'user_id': user_id},
                {'$set': {'user_id': user_id}},
                upsert=True
            )
            logger.info(f"👑 Admin added: {user_id}")
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
    
    async def remove_admin(self, user_id):
        if user_id == OWNER_ID:
            return False
        try:
            await self.admins.delete_one({'user_id': user_id})
            logger.info(f"👑 Admin removed: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            return False
    
    async def is_admin(self, user_id):
        if user_id == OWNER_ID:
            return True
        try:
            admin = await self.admins.find_one({'user_id': user_id})
            return bool(admin)
        except Exception as e:
            logger.error(f"Error checking admin: {e}")
            return False
    
    async def get_all_admins(self):
        try:
            cursor = self.admins.find({})
            admins = await cursor.to_list(length=None)
            return [a['user_id'] for a in admins]
        except Exception as e:
            logger.error(f"Error getting admins: {e}")
            return []
    
    # ==================== FILE STORE FUNCTIONS ====================
    
    def generate_file_id(self):
        chars = string.ascii_letters + string.digits
        return 'get-' + ''.join(random.choices(chars, k=12))
    
    async def store_file(self, file_data, user_id):
        try:
            file_id = self.generate_file_id()
            
            # Check if already exists
            existing = await self.files.find_one({'file_unique_id': file_data.file_unique_id})
            if existing:
                return existing['file_id']
            
            # Get chat and message info
            chat_id = getattr(file_data, 'chat', None)
            if chat_id:
                chat_id = chat_id.id
            else:
                chat_id = 0
            
            message_id = getattr(file_data, 'message_id', 0)
            
            await self.files.insert_one({
                'file_id': file_id,
                'message_id': message_id,
                'chat_id': chat_id,
                'file_unique_id': file_data.file_unique_id,
                'file_type': file_data.__class__.__name__.lower(),
                'caption': getattr(file_data, 'caption', None),
                'stored_by': user_id,
                'stored_at': datetime.datetime.now(),
                'short_url': None,
                'access_count': 0
            })
            
            logger.info(f"📁 File stored: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Error storing file: {e}")
            return None
    
    async def get_file(self, file_id):
        try:
            return await self.files.find_one({'file_id': file_id})
        except Exception as e:
            logger.error(f"Error getting file: {e}")
            return None
    
    async def get_file_by_unique_id(self, unique_id):
        try:
            return await self.files.find_one({'file_unique_id': unique_id})
        except Exception as e:
            logger.error(f"Error getting file by unique ID: {e}")
            return None
    
    async def increment_access(self, file_id):
        try:
            await self.files.update_one(
                {'file_id': file_id},
                {'$inc': {'access_count': 1}}
            )
        except Exception as e:
            logger.error(f"Error incrementing access: {e}")
    
    async def get_all_files(self):
        try:
            cursor = self.files.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting all files: {e}")
            return []
    
    async def total_files_count(self):
        try:
            return await self.files.count_documents({})
        except Exception as e:
            logger.error(f"Error counting files: {e}")
            return 0
    
    # ==================== SHORTENER FUNCTIONS ====================
    
    async def save_short_url(self, file_id, short_url):
        try:
            await self.files.update_one(
                {'file_id': file_id},
                {'$set': {'short_url': short_url}}
            )
        except Exception as e:
            logger.error(f"Error saving short URL: {e}")
    
    async def get_short_url(self, file_id):
        try:
            file = await self.files.find_one({'file_id': file_id})
            return file.get('short_url') if file else None
        except Exception as e:
            logger.error(f"Error getting short URL: {e}")
            return None
    
    async def refresh_all_short_urls(self):
        try:
            await self.files.update_many(
                {},
                {'$set': {'short_url': None}}
            )
            logger.info("🔄 All short URLs cleared for refresh")
        except Exception as e:
            logger.error(f"Error refreshing URLs: {e}")
    
    # ==================== SETTINGS FUNCTIONS ====================
    
    async def set_tutorial(self, url):
        try:
            await self.settings.update_one(
                {'key': 'tutorial'},
                {'$set': {'value': url}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error setting tutorial: {e}")
    
    async def get_tutorial(self):
        try:
            setting = await self.settings.find_one({'key': 'tutorial'})
            return setting.get('value') if setting else None
        except Exception as e:
            logger.error(f"Error getting tutorial: {e}")
            return None
    
    async def set_shortener_api(self, api_key):
        try:
            await self.settings.update_one(
                {'key': 'shortener_api'},
                {'$set': {'value': api_key}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error setting shortener API: {e}")
    
    async def get_shortener_api(self):
        try:
            setting = await self.settings.find_one({'key': 'shortener_api'})
            return setting.get('value') if setting else None
        except Exception as e:
            logger.error(f"Error getting shortener API: {e}")
            return None
    
    async def set_shortener_url(self, url):
        try:
            await self.settings.update_one(
                {'key': 'shortener_url'},
                {'$set': {'value': url}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error setting shortener URL: {e}")
    
    async def get_shortener_url(self):
        try:
            setting = await self.settings.find_one({'key': 'shortener_url'})
            return setting.get('value') if setting else None
        except Exception as e:
            logger.error(f"Error getting shortener URL: {e}")
            return None

# Initialize database
try:
    db = Database(DB_URI, DB_NAME)
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    # Create a dummy db for fallback
    class DummyDB:
        async def add_user(self, *args, **kwargs): pass
        async def is_admin(self, *args, **kwargs): return False
        async def check_premium(self, *args, **kwargs): return False
        # Add other methods as needed
    db = DummyDB()
