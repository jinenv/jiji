# bot.py - THE ONLY BOT FILE YOU NEED - UNICODE FIXED
import disnake
from disnake.ext import commands
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# FIXED: Configure logging with proper Unicode support
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s',
    handlers=[
        # Unicode-safe console handler
        logging.StreamHandler(sys.stdout),
        # UTF-8 file handler
        logging.FileHandler('logs/bot.log', mode='a', encoding='utf-8')
    ]
)

logging.getLogger("disnake.gateway").setLevel(logging.WARNING)
logging.getLogger("disnake.client").setLevel(logging.WARNING)
logging.getLogger("disnake.http").setLevel(logging.WARNING)
logging.getLogger("src.utils.database_service").setLevel(logging.WARNING)
logging.getLogger("src.utils.redis_service").setLevel(logging.WARNING) 
logging.getLogger("src.utils.emoji_manager").setLevel(logging.WARNING)
logging.getLogger("disnake.voice").setLevel(logging.ERROR)


# Set console encoding to UTF-8 for Windows
if sys.platform == "win32":
    try:
        # Try to set console to UTF-8
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Fallback for older Python versions
        pass

logger = logging.getLogger("reve")

# Import our stuff AFTER path is set
from src.utils.database_service import DatabaseService
from src.utils.config_manager import ConfigManager
from src.utils.redis_service import RedisService

# Bot setup
intents = disnake.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.InteractionBot(intents=intents)

@bot.event
async def on_ready():
    """Bot startup"""
    logger.info(f"{bot.user} is online!")
    logger.info(f"Connected to {len(bot.guilds)} guilds")
    
    # Status
    await bot.change_presence(
        activity=disnake.Game(name="with esprits | /start"),
        status=disnake.Status.online
    )
    
    # Initialize emoji manager with ABSOLUTE PATH
    try:
        from src.utils.emoji_manager import EmojiStorageManager
        
        # Get the ACTUAL config path
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "config", "emoji_mapping.json")

        logger.info(f"Looking for emoji config at: {config_path}")
        
        if os.path.exists(config_path):
            emoji_manager = EmojiStorageManager(bot, config_path)
            
            # Use the sync method instead - no await needed
            emoji_manager.set_emoji_servers([1369489835860955329])
            
            logger.info("Emoji manager initialized!")
        else:
            logger.warning(f"Emoji config not found at {config_path}")
            
    except Exception as e:
        logger.error(f"Failed to setup emoji manager: {e}")

def load_cogs():
    """Load all cogs"""
    cogs_dir = Path("src/cogs")
    
    for cog_file in cogs_dir.glob("*.py"):
        if cog_file.name.startswith("__"):
            continue
            
        cog_name = cog_file.stem
        try:
            bot.load_extension(f"src.cogs.{cog_name}")
            logger.info(f"Loaded: {cog_name}")
        except Exception as e:
            logger.error(f"Failed to load {cog_name}: {e}")

def initialize_services():
    """Initialize all services"""
    try:
        # Config Manager - ACTUALLY INITIALIZE IT
        from src.utils.config_manager import ConfigManager
        ConfigManager.load_all()  # ADD THIS
        logger.info(f"ConfigManager loaded: {len(ConfigManager._configs)} configs")
        
        # Database - ACTUALLY INITIALIZE IT
        from src.utils.database_service import DatabaseService
        DatabaseService.init()  # ADD THIS
        logger.info("DatabaseService ready")
        
        # Redis - ACTUALLY INITIALIZE IT
        from src.utils.redis_service import RedisService
        RedisService.init()  # ADD THIS TOO WHY NOT
        if RedisService.is_available():
            logger.info("RedisService connected")
        else:
            logger.warning("Redis not available - running without cache")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")

def main():
    """Main entry point"""
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Initialize services
    logger.info("Starting Reve...")
    initialize_services()
    
    # Load cogs
    load_cogs()
    
    # Get token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found!")
        sys.exit(1)
    
    # Run bot
    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()