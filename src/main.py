# src/main.py
import os
import logging
import asyncio
from dotenv import load_dotenv

from src.bot import run_bot 
from src.utils.database_service import DatabaseService
from src.utils.redis_service import RedisService
from src.utils.config_manager import ConfigManager

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """The main entry point for the bot."""
    load_dotenv()
    logger.info("Starting up Nyxa...")

    # Initialize services
    logger.info("Initializing services...")
    
    # Load configs (synchronous)
    ConfigManager.load_all()
    logger.info("ConfigManager loaded.")
    
    # Initialize database
    DatabaseService.init()
    logger.info("DatabaseService initialized.")
    
    # Initialize Redis (optional)
    try:
        RedisService.init()
        logger.info("RedisService initialized.")
    except Exception as e:
        logger.warning(f"Redis not available, continuing without cache: {e}")
    
    # Run the bot (this will block)
    run_bot()