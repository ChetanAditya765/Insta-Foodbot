from bot.InstagramFoodBot import InstagramFoodBot
from config.settings import INSTAGRAM_CREDENTIALS, MONGODB_URI
from database.mongodb import init_collections
import logging
import sys
import time

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('food_bot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('MainScript')

def main():
    logger = setup_logging()
    
    try:
        # Initialize database collections
        init_collections()
        
        # Initialize bot with retry logic
        max_retries = 3
        retry_delay = 30  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to initialize bot (attempt {attempt + 1}/{max_retries})")
                bot = InstagramFoodBot(INSTAGRAM_CREDENTIALS, MONGODB_URI)
                logger.info("Bot initialized successfully!")
                return bot
                
            except Exception as e:
                logger.error(f"Failed to initialize bot: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Exiting.")
                    raise
                    
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    bot = main()