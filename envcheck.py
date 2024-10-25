import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch environment variables
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
MONGODB_URI = os.getenv("MONGODB_URI")

# Step 1: Check if environment variables are loaded correctly
if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD or not MONGODB_URI:
    print("Error: Environment variables not loaded correctly. Please check .env file.")
else:
    print("Environment variables loaded successfully.")

# Step 2: Test MongoDB Connection
try:
    client = MongoClient(MONGODB_URI)
    # Attempt to list databases as a connection check
    databases = client.list_database_names()
    print("MongoDB connection successful. Databases:", databases)
except Exception as e:
    print("MongoDB connection failed:", e)

# Step 3: Check Instagram Credentials (Mock login for testing)
# Import your Instagram bot here
try:
    from bot.InstagramFoodBot import InstagramFoodBot  # Adjust path if necessary
    bot = InstagramFoodBot(username=INSTAGRAM_USERNAME, password=INSTAGRAM_PASSWORD)
    bot.login()
    print("Instagram login successful.")
except Exception as e:
    print("Instagram login failed:", e)
