import motor.motor_asyncio
import datetime
import random
import string
from config import DB_URI, DB_NAME, OWNER_ID

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.links = self.db.links
        self.users = self.db.users
        self.settings = self.db.settings
    
    # ==================== LINK STORE FUNCTIONS ====================
    
    def generate_hash(self, length=12):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))
    
    async def store_link(self, original_url: str, user_id: int):
        try:
            # Check if already exists
            existing = await self.links.find_one({'original_url': original_url})
            if existing:
                return existing['hash_id']
            
            # Generate unique hash
            hash_id = self.generate_hash()
            
            # Store in database
            await self.links.insert_one({
                'hash_id': hash_id,
                'original_url': original_url,
                'created_by': user_id,
                'created_at': datetime.datetime.now(),
                'access_count': 0,
                'short_url': None
            })
            
            return hash_id
        except Exception as e:
            print(f"Error storing link: {e}")
            return None
    
    async def get_original_url(self, hash_id: str):
        try:
            link = await self.links.find_one({'hash_id': hash_id})
            if link:
                # Increment access count
                await self.links.update_one(
                    {'hash_id': hash_id},
                    {'$inc': {'access_count': 1}}
                )
                return link.get('original_url')
            return None
        except Exception as e:
            print(f"Error getting original URL: {e}")
            return None
    
    async def save_short_url(self, hash_id: str, short_url: str):
        try:
            await self.links.update_one(
                {'hash_id': hash_id},
                {'$set': {'short_url': short_url}}
            )
        except Exception as e:
            print(f"Error saving short URL: {e}")
    
    async def get_short_url(self, hash_id: str):
        try:
            link = await self.links.find_one({'hash_id': hash_id})
            return link.get('short_url') if link else None
        except Exception as e:
            print(f"Error getting short URL: {e}")
            return None
    
    async def get_all_links(self):
        try:
            cursor = self.links.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting all links: {e}")
            return []
    
    async def total_links_count(self):
        try:
            return await self.links.count_documents({})
        except Exception as e:
            print(f"Error counting links: {e}")
            return 0
    
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
                    'total_links': 0
                })
        except Exception as e:
            print(f"Error adding user: {e}")
    
    async def get_user(self, user_id):
        try:
            return await self.users.find_one({'user_id': user_id})
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    async def increment_user_links(self, user_id):
        try:
            await self.users.update_one(
                {'user_id': user_id},
                {'$inc': {'total_links': 1}},
                upsert=True
            )
        except Exception as e:
            print(f"Error incrementing user links: {e}")
    
    # ==================== SETTINGS FUNCTIONS ====================
    
    async def set_shortener_api(self, api_key):
        try:
            await self.settings.update_one(
                {'key': 'shortener_api'},
                {'$set': {'value': api_key}},
                upsert=True
            )
        except Exception as e:
            print(f"Error setting shortener API: {e}")
    
    async def get_shortener_api(self):
        try:
            setting = await self.settings.find_one({'key': 'shortener_api'})
            return setting.get('value') if setting else None
        except Exception as e:
            print(f"Error getting shortener API: {e}")
            return None
    
    async def set_shortener_url(self, url):
        try:
            await self.settings.update_one(
                {'key': 'shortener_url'},
                {'$set': {'value': url}},
                upsert=True
            )
        except Exception as e:
            print(f"Error setting shortener URL: {e}")
    
    async def get_shortener_url(self):
        try:
            setting = await self.settings.find_one({'key': 'shortener_url'})
            return setting.get('value') if setting else None
        except Exception as e:
            print(f"Error getting shortener URL: {e}")
            return None

# Initialize database
db = Database(DB_URI, DB_NAME)
