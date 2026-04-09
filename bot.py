import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ErrorEvent

from config import Config
from database import db
from handlers import router

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

# Initialize bot
bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
dp.include_router(router)

@dp.error()
async def error_handler(event: ErrorEvent):
    """Global error handler"""
    logger.error(f"Error: {event.exception}", exc_info=True)
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer("An error occurred. Please try again.", show_alert=True)
        elif event.update.message:
            await event.update.message.answer("❌ An error occurred. Please try /start")
    except:
        pass

async def on_startup():
    """Startup actions"""
    logger.info("🚀 Bot starting...")
    try:
        db.init_database()
        logger.info("✅ Database initialized")
        for admin_id in Config.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, "🤖 <b>Bot Started!</b>\n\nUse /admin for admin panel")
                logger.info(f"✅ Notified admin {admin_id}")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

async def on_shutdown():
    """Shutdown actions"""
    logger.info("Bot shutting down...")
    await bot.session.close()

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")