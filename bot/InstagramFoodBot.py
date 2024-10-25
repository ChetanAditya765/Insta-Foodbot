from instagram_private_api import Client, ClientError, ClientLoginError
from pymongo import MongoClient
import logging
import json
import time
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import socket
import requests
import os
import sys
from dotenv import load_dotenv

class InstagramFoodBot:
    def __init__(self, credentials, mongodb_uri):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('food_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('InstagramFoodBot')
        
        # Initialize attributes
        self.username = credentials['username']
        self.password = credentials['password']
        self.api = None
        self.db_client = None
        self.db = None
        
        # Set default timeout
        socket.setdefaulttimeout(30)
        
        try:
            # Initialize Instagram API
            self.connect_to_instagram()
            
            # Initialize MongoDB
            self.connect_to_mongodb(mongodb_uri)
            
            self.logger.info("Bot initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {str(e)}")
            raise

    def test_internet_connection(self):
        """Test internet connectivity"""
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.RequestException:
            return False

    def connect_to_instagram(self):
    max_retries = 3
    retry_delay = 5  # seconds

    if not self.test_internet_connection():
        raise ConnectionError("No internet connection available")

    for attempt in range(max_retries):
        try:
            self.logger.info(f"Attempting to connect to Instagram (attempt {attempt + 1}/{max_retries})")
            
            # Settings for the Instagram client with generated UUIDs
            settings = {
                'device_id': str(uuid.uuid4()),
                'uuid': str(uuid.uuid4()),
                'user_agent': 'Instagram 76.0.0.15.395 Android (24/7.0; 640dpi; 1440x2560; samsung; SM-G930F; herolte; samsungexynos8890; en_US; 138226743)',
                'cookie': None,
                'settings': None,
            }
            
            self.api = Client(
                self.username,
                self.password,
                settings=settings
            )
            
            self.api.current_user()
            self.logger.info("Successfully connected to Instagram")
            return
            
        except ClientLoginError as e:
            self.logger.error(f"Instagram login failed: {str(e)}")
            if "challenge_required" in str(e):
                self.logger.error("Instagram requires verification. Please log in through the website first.")
            raise
            
        except ClientError as e:
            self.logger.error(f"Instagram connection failed: {str(e)} - Error code: {e.code}")
            if attempt < max_retries - 1:
                self.logger.warning(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                self.logger.error("Max retries reached for Instagram connection")
                raise
                
        except Exception as e:
            self.logger.error(f"Unexpected error during Instagram connection: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise


    def connect_to_mongodb(self, mongodb_uri):
        """Connect to MongoDB database"""
        try:
            self.db_client = MongoClient(mongodb_uri)
            # Test the connection
            self.db_client.server_info()
            self.db = self.db_client.food_ordering_db
            self.logger.info("Successfully connected to MongoDB")
        except Exception as e:
            self.logger.error(f"MongoDB connection failed: {str(e)}")
            raise

    def check_direct_messages(self):
        """Check and process new direct messages"""
        try:
            # Get direct inbox
            inbox = self.api.direct_v2_inbox()
            
            # Process each thread in the inbox
            for thread in inbox['inbox']['threads']:
                # Get thread items (messages)
                thread_id = thread['thread_id']
                thread_items = self.api.direct_v2_thread(thread_id=thread_id)['thread']['items']
                
                for item in thread_items:
                    # Process only text messages that haven't been processed
                    if (item['item_type'] == 'text' and 
                        'text' in item and 
                        not self.is_message_processed(item['item_id'])):
                        
                        message_text = item['text'].strip()
                        user_id = thread['users'][0]['pk']
                        
                        # Process the message
                        response = self.process_message(message_text)
                        
                        # Send response
                        if response:
                            self.send_message(response, thread_id)
                            
                        # Mark message as processed
                        self.mark_message_processed(item['item_id'])
                        
        except Exception as e:
            self.logger.error(f"Error checking direct messages: {str(e)}")
            raise

    def is_message_processed(self, message_id):
        """Check if a message has been processed"""
        try:
            result = self.db.processed_messages.find_one({'message_id': message_id})
            return bool(result)
        except Exception as e:
            self.logger.error(f"Error checking processed message: {str(e)}")
            return False

    def mark_message_processed(self, message_id):
        """Mark a message as processed"""
        try:
            self.db.processed_messages.insert_one({
                'message_id': message_id,
                'processed_at': datetime.utcnow()
            })
        except Exception as e:
            self.logger.error(f"Error marking message as processed: {str(e)}")

    def send_message(self, text, thread_id):
        """Send a message to a thread"""
        try:
            self.api.direct_v2_send(
                text=text,
                thread_ids=[thread_id]
            )
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            raise

    def process_message(self, message):
        """Process incoming Instagram messages"""
        try:
            command = message.lower().strip()
            
            if command == 'menu':
                return self.get_menu()
            elif command.startswith('order'):
                return self.process_order(message)
            elif command.startswith('track'):
                return self.track_order(message)
            else:
                return ("Welcome to our Food Bot! 🍽️\n\n"
                       "Available commands:\n"
                       "• Type 'menu' to see our menu\n"
                       "• Type 'order <item> x<quantity>' to place an order\n"
                       "• Type 'track <order-id>' to track your order")
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return "Sorry, I couldn't process your request. Please try again."

    def get_menu(self):
        """Retrieve and format menu items"""
        try:
            menu_items = self.db.menu.find({'available': True})
            menu_text = "🍽️ Our Menu:\n\n"
            
            for item in menu_items:
                menu_text += f"• {item['name']} - ${item['price']:.2f}\n"
                menu_text += f"  {item['description']}\n\n"
            
            menu_text += "\nTo order, type: order <item> x<quantity>"
            return menu_text
        except Exception as e:
            self.logger.error(f"Error retrieving menu: {str(e)}")
            return "Sorry, I couldn't retrieve the menu right now. Please try again later."

    def process_order(self, message):
        """Process order command"""
        try:
            # Simple order parsing
            parts = message.split('x')
            if len(parts) != 2:
                return "Please use the format: order <item> x<quantity>\nExample: order Margherita Pizza x2"
            
            item_name = parts[0].replace('order', '').strip()
            try:
                quantity = int(parts[1].strip())
                if quantity <= 0:
                    return "Please specify a quantity greater than 0"
            except ValueError:
                return "Please specify a valid quantity number"
            
            # Check if item exists
            menu_item = self.db.menu.find_one({'name': {'$regex': f'^{item_name}$', '$options': 'i'}})
            if not menu_item:
                return f"Sorry, '{item_name}' is not on our menu. Type 'menu' to see available items."
            
            # Create order
            order = {
                'item': menu_item['name'],
                'quantity': quantity,
                'total': menu_item['price'] * quantity,
                'status': 'pending',
                'timestamp': datetime.utcnow(),
            }
            
            result = self.db.orders.insert_one(order)
            
            return (f"Order received! 🎉\n\n"
                   f"Order details:\n"
                   f"• {quantity}x {menu_item['name']}\n"
                   f"• Total: ${order['total']:.2f}\n\n"
                   f"Your order ID is: {result.inserted_id}\n"
                   f"Track your order with: track {result.inserted_id}")
        except Exception as e:
            self.logger.error(f"Error processing order: {str(e)}")
            return "Sorry, I couldn't process your order. Please try again."

    def track_order(self, message):
        """Track order status"""
        try:
            order_id = message.replace('track', '').strip()
            try:
                order_id = ObjectId(order_id)
            except Exception:
                return "Please provide a valid order ID"
            
            order = self.db.orders.find_one({'_id': order_id})
            if not order:
                return "Order not found. Please check the ID and try again."
            
            return (f"Order Status:\n\n"
                   f"• Item: {order['item']}\n"
                   f"• Quantity: {order['quantity']}\n"
                   f"• Status: {order['status']}\n"
                   f"• Total: ${order['total']:.2f}\n"
                   f"• Placed on: {order['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            self.logger.error(f"Error tracking order: {str(e)}")
            return "Sorry, I couldn't retrieve your order status. Please try again later."

    def run(self):
        """Run the bot continuously"""
        self.logger.info("Bot is running")
        
        try:
            while True:
                self.check_direct_messages()
                time.sleep(10)  # Check messages every 10 seconds
                
                # Cleanup old processed messages (older than 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(days=1)
                self.db.processed_messages.delete_many({'processed_at': {'$lt': cutoff_time}})
                
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

# Load environment variables
load_dotenv()

# Set up bot credentials and MongoDB URI
credentials = {
    'username': os.getenv("INSTAGRAM_USERNAME"),
    'password': os.getenv("INSTAGRAM_PASSWORD")
}
mongodb_uri = os.getenv("MONGODB_URI")

# Initialize and run the bot
try:
    bot = InstagramFoodBot(credentials, mongodb_uri)
    bot.run()
except Exception as e:
    print(f"Error starting bot: {str(e)}")
