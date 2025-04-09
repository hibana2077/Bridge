import os
import json
from typing import Dict, Any, Optional, List
import redis
from cryptography.fernet import Fernet

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 0)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

# Encryption key for sensitive data
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    """Decrypt sensitive data"""
    return cipher_suite.decrypt(data.encode()).decode()

# API Key Management
def save_exchange_api_key(user_id: str, exchange: str, api_key: str, api_secret: str) -> bool:
    """Save encrypted exchange API keys to Redis"""
    key = f"user:{user_id}:exchange:{exchange}"
    data = {
        "api_key": encrypt_data(api_key),
        "api_secret": encrypt_data(api_secret)
    }
    return redis_client.set(key, json.dumps(data))

def get_exchange_api_key(user_id: str, exchange: str) -> Dict[str, str]:
    """Get decrypted exchange API keys from Redis"""
    key = f"user:{user_id}:exchange:{exchange}"
    data = redis_client.get(key)
    if not data:
        return {}
    
    encrypted_data = json.loads(data)
    return {
        "api_key": decrypt_data(encrypted_data["api_key"]),
        "api_secret": decrypt_data(encrypted_data["api_secret"])
    }

def delete_exchange_api_key(user_id: str, exchange: str) -> bool:
    """Delete exchange API keys from Redis"""
    key = f"user:{user_id}:exchange:{exchange}"
    return redis_client.delete(key) > 0

# Alert Configuration
def save_alert_config(user_id: str, config_name: str, config_data: Dict[str, Any]) -> bool:
    """Save alert configuration to Redis"""
    key = f"user:{user_id}:alert_config:{config_name}"
    return redis_client.set(key, json.dumps(config_data))

def get_alert_config(user_id: str, config_name: str) -> Dict[str, Any]:
    """Get alert configuration from Redis"""
    key = f"user:{user_id}:alert_config:{config_name}"
    data = redis_client.get(key)
    if not data:
        return {}
    return json.loads(data)

def get_all_alert_configs(user_id: str) -> List[Dict[str, Any]]:
    """Get all alert configurations for a user"""
    pattern = f"user:{user_id}:alert_config:*"
    keys = redis_client.keys(pattern)
    result = []
    for key in keys:
        config_name = key.split(":")[-1]
        config = get_alert_config(user_id, config_name)
        if config:
            config["name"] = config_name
            result.append(config)
    return result

def delete_alert_config(user_id: str, config_name: str) -> bool:
    """Delete alert configuration from Redis"""
    key = f"user:{user_id}:alert_config:{config_name}"
    return redis_client.delete(key) > 0

# Alert History
def save_alert_history(user_id: str, alert_data: Dict[str, Any]) -> bool:
    """Save alert execution history to Redis"""
    alert_id = f"alert:{user_id}:{alert_data['timestamp']}"
    return redis_client.set(alert_id, json.dumps(alert_data))

def get_alert_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get alert execution history from Redis"""
    pattern = f"alert:{user_id}:*"
    keys = redis_client.keys(pattern)
    # Sort by timestamp (descending)
    keys.sort(reverse=True)
    keys = keys[:limit]
    
    result = []
    for key in keys:
        data = redis_client.get(key)
        if data:
            result.append(json.loads(data))
    
    return result