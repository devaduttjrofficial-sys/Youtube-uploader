import logging
import config
from bot import app
from web_server import keep_alive
import importlib

# Ensure all handlers are registered
import bot
import upload_handlers

logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting web server...")
    keep_alive()
    logger.info("Starting Telegram bot...")
    app.run()
