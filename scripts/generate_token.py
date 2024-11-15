import hashlib
import secrets
import argparse

def generate_api_key():
    """Generate a random API key"""
    return secrets.token_urlsafe(32)

def hash_key(key: str) -> str:
    """Create SHA-256 hash of API key"""
    return hashlib.sha256(key.encode()).hexdigest()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate txtai API key and hash')
    parser.add_argument('--key', help='Use specific API key instead of generating one')
    args = parser.parse_args()
    
    # Generate or use provided key
    api_key = args.key if args.key else generate_api_key()
    api_hash = hash_key(api_key)
    
    print("\nAPI Key (for clients):")
    print(api_key)
    print("\nAPI Hash (for .env):")
    print(api_hash)
    print("\nAdd this line to your .env file:")
    print(f"API_KEY={api_hash}")