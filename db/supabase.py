"""
Supabase PostgreSQL Database Connection
Handles connection to Supabase database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

class SupabaseDB:
    """Supabase database connection handler"""
    
    _instance = None
    _client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseDB, cls).__new__(cls)
        return cls._instance
    
    def connect(self) -> Client:
        """Establish connection to Supabase"""
        try:
            if self._client is None:
                if not SUPABASE_URL or not SUPABASE_KEY:
                    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
                
                self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print(f"✓ Connected to Supabase")
            return self._client
        except Exception as e:
            print(f"✗ Failed to connect to Supabase: {e}")
            raise
    
    def get_client(self) -> Client:
        """Get Supabase client instance"""
        if self._client is None:
            return self.connect()
        return self._client

# Initialize database connection
db_instance = SupabaseDB()

def get_supabase() -> Client:
    """Helper function to get Supabase client instance"""
    return db_instance.get_client()
