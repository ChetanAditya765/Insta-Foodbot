from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

INSTAGRAM_CREDENTIALS = {
    'username': os.getenv('INSTAGRAM_USERNAME'),
    'password': os.getenv('INSTAGRAM_PASSWORD')
}

MONGODB_URI = os.getenv('MONGODB_URI')

# If MONGODB_URI is not set, use a default local connection
if not MONGODB_URI:
    MONGODB_URI = "mongodb://localhost:27017/foodOrdersDB"