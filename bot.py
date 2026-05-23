from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import config
import logging
import youtube

logger = logging.getLogger(__name__)

# Allowed users set
auth_users = set()
if config.BOT_OWNER:
    auth_users.add(int(config.BOT_OWNER))
if config.AUTH_USERS:
    for uid in config.AUTH_USERS.split(','):
        if uid.strip().isdigit():
            auth_users.add(int(uid.strip()))


def is_authorized(user_id):
    return user_id in auth_users


app = Client(
    config.SESSION_NAME,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    if not is_authorized(message.from_user.id):
        await message.reply_text("You are not authorized to use this bot.")
        return

    text = (
        "Hello! I am a Telegram to YouTube uploader bot.\n\n"
        "To get started, please use /authorize to link your YouTube channel.\n"
        "Once authorized, you can just send me a video to upload it."
    )
    await message.reply_text(text)


@app.on_message(filters.command("help") & filters.private)
async def help_cmd(client: Client, message: Message):
    if not is_authorized(message.from_user.id):
        return

    text = (
        "**Available Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/authorize - Authorize your YouTube channel\n"
        "\n"
        "Just send a video to start the upload process!"
    )
    await message.reply_text(text)


@app.on_message(filters.command("authorize") & filters.private)
async def authorize_cmd(client: Client, message: Message):
    if not is_authorized(message.from_user.id):
        return

    # If already authorized, youtube.get_authenticated_service will return a
    # service
    try:
        service = youtube.get_authenticated_service()
        if service:
            await message.reply_text("Your YouTube channel is already authorized!")
            return
    except Exception as e:
        logger.warning(f"Error checking auth: {e}")

    try:
        url = youtube.get_auth_url()
        text = (
            "Please authorize the bot by visiting the following link:\n\n"
            f"{url}\n\n"
            "After you authorize, Google will redirect you to a page (which might say 'Unable to connect' or 'localhost refused to connect'). "
            "Copy the ENTIRE URL of that page and send it here using the command:\n"
            "`/authcode THE_FULL_URL`"
        )
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"Error generating auth URL: {e}")


@app.on_message(filters.command("authcode") & filters.private)
async def authcode_cmd(client: Client, message: Message):
    if not is_authorized(message.from_user.id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text("Please provide the code like this: `/authcode THE_FULL_URL`")
        return

    code = parts[1].strip()
    try:
        youtube.authorize(code)
        await message.reply_text("Authorization successful! You can now send me videos to upload.")
    except Exception as e:
        await message.reply_text(f"Authorization failed: {e}")
