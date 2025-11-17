
import os
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# MongoDB connection
MONGODB_URI = os.environ.get('MONGODB_URI')

if not MONGODB_URI:
    raise ValueError(
        "MONGODB_URI environment variable not set! "
        "Please add your MongoDB connection string to Secrets."
    )

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ping')
    db = client['fb_e2ee_automation']
except Exception as e:
    raise ConnectionError(f"Failed to connect to MongoDB: {e}")

# Collections
users_collection = db['users']
sessions_collection = db['sessions']
automation_locks_collection = db['automation_locks']

# Create indexes
users_collection.create_index('username', unique=True)
sessions_collection.create_index('token', unique=True)
sessions_collection.create_index('expires_at')
automation_locks_collection.create_index('user_id', unique=True)

# Instance ID for distributed execution
INSTANCE_ID = str(uuid.uuid4())

def get_instance_id():
    """Get unique instance ID for this process"""
    return INSTANCE_ID

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    """Create a new user"""
    try:
        hashed_pw = hash_password(password)
        user_data = {
            'user_id': str(uuid.uuid4()),
            'username': username,
            'password': hashed_pw,
            'chat_id': '',
            'name_prefix': '',
            'delay': 20,
            'cookies': '',
            'messages': 'hindi',
            'automation_running': False,
            'created_at': datetime.utcnow()
        }
        users_collection.insert_one(user_data)
        return True, "Account created successfully!"
    except DuplicateKeyError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

def verify_user(username, password):
    """Verify user credentials and return user_id"""
    hashed_pw = hash_password(password)
    user = users_collection.find_one({'username': username, 'password': hashed_pw})
    return user['user_id'] if user else None

def get_username(user_id):
    """Get username from user_id"""
    user = users_collection.find_one({'user_id': user_id})
    return user['username'] if user else None

def create_session_token(user_id, expiry_hours=168):
    """Create session token for user"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
    
    sessions_collection.insert_one({
        'token': token,
        'user_id': user_id,
        'created_at': datetime.utcnow(),
        'expires_at': expires_at
    })
    return token

def validate_session_token(token):
    """Validate session token and return user data"""
    session = sessions_collection.find_one({'token': token})
    if not session:
        return None
    
    if datetime.utcnow() > session['expires_at']:
        sessions_collection.delete_one({'token': token})
        return None
    
    user = users_collection.find_one({'user_id': session['user_id']})
    return user if user else None

def revoke_session_token(token):
    """Revoke a session token"""
    sessions_collection.delete_one({'token': token})

def cleanup_expired_sessions():
    """Remove expired sessions"""
    sessions_collection.delete_many({'expires_at': {'$lt': datetime.utcnow()}})

def get_user_config(user_id):
    """Get user configuration"""
    user = users_collection.find_one({'user_id': user_id})
    if not user:
        return None
    
    return {
        'user_id': user_id,
        'username': user.get('username', ''),
        'chat_id': user.get('chat_id', ''),
        'name_prefix': user.get('name_prefix', ''),
        'delay': user.get('delay', 20),
        'cookies': user.get('cookies', ''),
        'messages': user.get('messages', 'hindi'),
        'automation_running': user.get('automation_running', False)
    }

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    """Update user configuration"""
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {
            'chat_id': chat_id,
            'name_prefix': name_prefix,
            'delay': delay,
            'cookies': cookies,
            'messages': messages
        }}
    )

def set_automation_running(user_id, running):
    """Set automation running status"""
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'automation_running': running}}
    )

def get_automation_running(user_id):
    """Get automation running status"""
    user = users_collection.find_one({'user_id': user_id})
    return user.get('automation_running', False) if user else False

def save_automation_logs(user_id, logs):
    """Save automation logs"""
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'logs': logs}}
    )

def get_automation_logs(user_id):
    """Get automation logs"""
    user = users_collection.find_one({'user_id': user_id})
    return user.get('logs', []) if user else []

def clear_automation_logs(user_id):
    """Clear automation logs"""
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'logs': []}}
    )

def get_all_running_users():
    """Get all users with automation_running=True"""
    return list(users_collection.find({'automation_running': True}))

def acquire_automation_lock(user_id, ttl_seconds=60):
    """Acquire distributed lock for automation"""
    try:
        automation_locks_collection.insert_one({
            'user_id': user_id,
            'instance_id': INSTANCE_ID,
            'acquired_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl_seconds)
        })
        return True
    except DuplicateKeyError:
        return False

def release_automation_lock(user_id):
    """Release distributed lock"""
    automation_locks_collection.delete_one({'user_id': user_id, 'instance_id': INSTANCE_ID})

def update_instance_heartbeat(user_id, instance_id, ttl_seconds=60):
    """Update heartbeat for instance"""
    result = automation_locks_collection.update_one(
        {'user_id': user_id, 'instance_id': instance_id},
        {'$set': {'expires_at': datetime.utcnow() + timedelta(seconds=ttl_seconds)}}
    )
    return result.modified_count > 0

def get_lock_owner(user_id):
    """Get instance_id that owns the lock"""
    lock = automation_locks_collection.find_one({'user_id': user_id})
    return lock['instance_id'] if lock else None

def cleanup_expired_locks():
    """Remove expired locks"""
    automation_locks_collection.delete_many({'expires_at': {'$lt': datetime.utcnow()}})

def register_automation_instance(user_id, instance_id, ttl_seconds=60):
    """Register automation instance (supports parallel execution)"""
    # This is a simplified version - just return True for now
    return True

def remove_automation_instance(user_id, instance_id):
    """Remove automation instance registration"""
    pass

def get_active_instances(user_id):
    """Get list of active instances for user"""
    return []

def clear_all_database_data():
    """Clear all data from database - ADMIN ONLY"""
    try:
        stats = {}
        stats['users'] = users_collection.delete_many({}).deleted_count
        stats['sessions'] = sessions_collection.delete_many({}).deleted_count
        stats['locks'] = automation_locks_collection.delete_many({}).deleted_count
        
        return True, "All database data cleared successfully!", stats
    except Exception as e:
        return False, f"Error clearing database: {str(e)}", {}
