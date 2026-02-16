import motor.motor_asyncio
import datetime
import random
import string
import hashlib
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
        """Generate random hash for short link"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))
    
    async def store_link(self, original_url: str, user_id: int):
        """Store original link and return hash"""
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
            'short_url': None  # Will be filled by shortener
        })
        
        return hash_id
    
    async def get_original_url(self, hash_id: str):
        """Get original URL from hash"""
        link = await self.links.find_one({'hash_id': hash_id})
        if link:
            # Increment access count
            await self.links.update_one(
                {'hash_id': hash_id},
                {'$inc': {'access_count': 1}}
            )
            return link.get('original_url')
        return None
    
    async def save_short_url(self, hash_id: str, short_url: str):
        """Save generated short URL"""
        await self.links.update_one(
            {'hash_id': hash_id},
            {'$set': {'short_url': short_url}}
        )
    
    async def get_short_url(self, hash_id: str):
        """Get short URL for hash"""
        link = await self.links.find_one({'hash_id': hash_id})
        return link.get('short_url') if link else None
    
    async def get_all_links(self):
        """Get all stored links"""
        cursor = self.links.find({})
        return await cursor.to_list(length=None)
    
    async def total_links_count(self):
        return await self.links.count_documents({})
    
    # ==================== USER FUNCTIONS ====================
    
    async def add_user(self, user_id, username=None, first_name=None):
        user = await self.users.find_one({'user_id': user_id})
        if not user:
            await self.users.insert_one({
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'joined_date': datetime.datetime.now(),
                'total_links': 0
            })
    
    async def get_user(self, user_id):
        return await self.users.find_one({'user_id': user_id})
    
    async def increment_user_links(self, user_id):
        await self.users.update_one(
            {'user_id': user_id},
            {'$inc': {'total_links': 1}}
        )
    
    # ==================== SETTINGS FUNCTIONS ====================
    
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
