import asyncio
import ffmpeg_utils
import youtube
from pyrogram.errors import MessageNotModified
import time
import os
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot import app, is_authorized
from state_manager import get_user_data, update_user_data, reset_user_data
import config


@app.on_message(filters.video & filters.private)
async def handle_video(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    file_id = message.video.file_id
    file_name = message.video.file_name or "video.mp4"

    update_user_data(user_id,
                     state="AWAITING_TITLE",
                     file_id=file_id,
                     file_name=file_name,
                     video_message_id=message.id)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Skip Title (Use filename)", callback_data="title_skip")],
        [InlineKeyboardButton("Cancel Upload", callback_data="cancel_upload")]
    ])

    await message.reply_text(
        f"Received video: `{file_name}`\n\n"
        "Please send me the custom **TITLE** for the video, or choose an option below:",
        reply_markup=keyboard
    )


@app.on_message(filters.text & filters.private, group=1)
async def handle_text_input(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    if message.text.startswith('/'):
        return

    data = get_user_data(user_id)
    state = data.get("state")

    if state == "AWAITING_TITLE":
        title = message.text.strip()
        update_user_data(user_id, title=title, state="AWAITING_DESC")
        await prompt_description(message)
    elif state == "AWAITING_DESC":
        desc = message.text.strip()
        update_user_data(user_id, description=desc, state="AWAITING_PRIVACY")
        await prompt_privacy(message)


async def prompt_description(message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Skip Description", callback_data="desc_skip")],
        [InlineKeyboardButton("Cancel Upload", callback_data="cancel_upload")]
    ])
    await message.reply_text(
        "Great! Now send me the custom **DESCRIPTION**, or skip.",
        reply_markup=keyboard
    )


async def prompt_privacy(message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Public", callback_data="priv_public"),
         InlineKeyboardButton("Private", callback_data="priv_private"),
         InlineKeyboardButton("Unlisted", callback_data="priv_unlisted")],
        [InlineKeyboardButton("Cancel Upload", callback_data="cancel_upload")]
    ])
    await message.reply_text(
        "Choose the **PRIVACY** status for your video:",
        reply_markup=keyboard
    )


async def prompt_category(message: Message):
    # For simplicity, providing a few common categories + Skip option
    # 20 = Gaming, 22 = People & Blogs, 24 = Entertainment, 27 = Education
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Gaming", callback_data="cat_20"),
         InlineKeyboardButton("People & Blogs", callback_data="cat_22")],
        [InlineKeyboardButton("Entertainment", callback_data="cat_24"),
         InlineKeyboardButton("Education", callback_data="cat_27")],
        [InlineKeyboardButton("Skip (Default: 22)", callback_data="cat_skip")],
        [InlineKeyboardButton("Cancel Upload", callback_data="cancel_upload")]
    ])
    await message.reply_text(
        "Choose a **CATEGORY**:",
        reply_markup=keyboard
    )


async def prompt_thumbnail(message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Custom Thumbnail", callback_data="thumb_custom")],
        [InlineKeyboardButton("Auto (Extract Frame)", callback_data="thumb_auto")],
        [InlineKeyboardButton("No Thumbnail", callback_data="thumb_skip")],
        [InlineKeyboardButton("Cancel Upload", callback_data="cancel_upload")]
    ])
    await message.reply_text(
        "Choose a **THUMBNAIL** option:",
        reply_markup=keyboard
    )


async def prompt_subtitles(message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Use Built-in Subtitles", callback_data="sub_builtin")],
        [InlineKeyboardButton("Upload Separate .srt", callback_data="sub_separate")],
        [InlineKeyboardButton("No Subtitles", callback_data="sub_skip")],
        [InlineKeyboardButton("Cancel Upload", callback_data="cancel_upload")]
    ])
    await message.reply_text(
        "Choose a **SUBTITLE** option:",
        reply_markup=keyboard
    )


@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.answer("Not authorized", show_alert=True)
        return

    data = get_user_data(user_id)
    cdata = query.data

    if cdata == "cancel_upload":
        reset_user_data(user_id)
        await query.message.edit_text("Upload cancelled.")
        return

    if cdata == "title_skip" and data.get("state") == "AWAITING_TITLE":
        title = data.get("file_name", "video")
        # Apply prefix/suffix if config has them
        title = f"{config.VIDEO_TITLE_PREFIX}{title}{config.VIDEO_TITLE_SUFFIX}"
        update_user_data(user_id, title=title, state="AWAITING_DESC")
        await query.message.edit_text(f"Title skipped. Using: `{title}`")
        await prompt_description(query.message)
        return

    if cdata == "desc_skip" and data.get("state") == "AWAITING_DESC":
        desc = config.VIDEO_DESCRIPTION
        update_user_data(user_id, description=desc, state="AWAITING_PRIVACY")
        await query.message.edit_text("Description skipped.")
        await prompt_privacy(query.message)
        return

    if cdata.startswith("priv_") and data.get("state") == "AWAITING_PRIVACY":
        privacy = cdata.split("_")[1]
        update_user_data(user_id, privacy=privacy, state="AWAITING_CATEGORY")
        await query.message.edit_text(f"Privacy set to: **{privacy}**")
        await prompt_category(query.message)
        return

    if cdata.startswith("cat_") and data.get("state") == "AWAITING_CATEGORY":
        cat = "22" if cdata == "cat_skip" else cdata.split("_")[1]
        if not cat and config.VIDEO_CATEGORY:
            cat = config.VIDEO_CATEGORY
        update_user_data(user_id, category=cat, state="AWAITING_THUMBNAIL")
        await query.message.edit_text(f"Category set to ID: **{cat}**")
        await prompt_thumbnail(query.message)
        return

    if cdata.startswith("thumb_") and data.get(
            "state") == "AWAITING_THUMBNAIL":
        mode = cdata.split("_")[1]
        if mode == "custom":
            update_user_data(
                user_id,
                thumbnail_mode="CUSTOM",
                state="AWAITING_CUSTOM_THUMB")
            await query.message.edit_text("Please send me the **thumbnail image** (JPG/PNG).")
            return
        else:
            update_user_data(
                user_id,
                thumbnail_mode=mode.upper(),
                state="AWAITING_SUBTITLES")
            await query.message.edit_text(f"Thumbnail mode: **{mode.upper()}**")
            await prompt_subtitles(query.message)
            return

    if cdata.startswith("sub_") and data.get("state") == "AWAITING_SUBTITLES":
        mode = cdata.split("_")[1]
        if mode == "separate":
            update_user_data(
                user_id,
                subtitle_mode="SEPARATE",
                state="AWAITING_SRT")
            await query.message.edit_text("Please send me the **.srt or .vtt** file.")
            return
        elif mode == "builtin":
            update_user_data(user_id, subtitle_mode="BUILT_IN", state="READY")
            await query.message.edit_text("Will attempt to use built-in subtitles. Ready to upload!\n\nSend `/upload` to confirm.")
            return
        else:
            update_user_data(user_id, subtitle_mode="NONE", state="READY")
            await query.message.edit_text("No subtitles. Ready to upload!\n\nSend `/upload` to confirm.")
            return


@app.on_message(filters.photo & filters.private)
async def handle_photo(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    data = get_user_data(user_id)
    if data.get("state") == "AWAITING_CUSTOM_THUMB":
        file_id = message.photo.file_id
        update_user_data(
            user_id,
            custom_thumb_file_id=file_id,
            state="AWAITING_SUBTITLES")
        await message.reply_text("Custom thumbnail received.")
        await prompt_subtitles(message)


@app.on_message(filters.document & filters.private)
async def handle_document(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    data = get_user_data(user_id)
    if data.get("state") == "AWAITING_SRT":
        if message.document.file_name.endswith((".srt", ".vtt")):
            file_id = message.document.file_id
            update_user_data(
                user_id,
                separate_srt_file_id=file_id,
                state="READY")
            await message.reply_text("Subtitle file received. Ready to upload!\n\nSend `/upload` to confirm.")
        else:
            await message.reply_text("Please send a valid .srt or .vtt file.")


async def progress_bar(current, total, msg, text="Downloading..."):
    # Simple rate-limiting to avoid flooding Telegram
    now = time.time()
    if hasattr(msg, "last_edit_time"):
        if now - msg.last_edit_time < 2.0 and current < total:
            return

    percent = current * 100 / total
    try:
        await msg.edit_text(f"{text} {percent:.1f}%")
        msg.last_edit_time = now
    except MessageNotModified:
        pass
    except Exception:
        pass


@app.on_message(filters.command("upload") & filters.private)
async def confirm_upload(client: Client, message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    data = get_user_data(user_id)
    if data.get("state") != "READY":
        await message.reply_text("You haven't completed the setup. Send a video first.")
        return

    status_msg = await message.reply_text("Starting download from Telegram...")

    video_file_id = data["file_id"]
    file_name = data["file_name"]
    title = data["title"]
    description = data.get("description", "")
    privacy = data["privacy"]
    category = data["category"]
    thumbnail_mode = data.get("thumbnail_mode", "NONE")
    subtitle_mode = data.get("subtitle_mode", "NONE")

    downloads_dir = "downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    video_path = os.path.join(downloads_dir, f"{user_id}_{file_name}")

    try:
        # 1. Download Video
        await client.download_media(
            message=video_file_id,
            file_name=video_path,
            progress=progress_bar,
            progress_args=(status_msg, "Downloading Video...")
        )

        # 2. Process Thumbnail
        thumbnail_path = None
        if thumbnail_mode == "CUSTOM" and data.get("custom_thumb_file_id"):
            await status_msg.edit_text("Downloading custom thumbnail...")
            thumb_path_temp = os.path.join(
                downloads_dir, f"{user_id}_thumb.jpg")
            thumbnail_path = await client.download_media(
                message=data["custom_thumb_file_id"],
                file_name=thumb_path_temp
            )
        elif thumbnail_mode == "AUTO":
            await status_msg.edit_text("Extracting auto-thumbnail via FFmpeg...")
            thumbnail_path = await asyncio.to_thread(ffmpeg_utils.generate_thumbnail, video_path, downloads_dir)

        # 3. Process Subtitles
        subtitle_path = None
        if subtitle_mode == "SEPARATE" and data.get("separate_srt_file_id"):
            await status_msg.edit_text("Downloading subtitle file...")
            srt_path_temp = os.path.join(downloads_dir, f"{user_id}_sub.srt")
            subtitle_path = await client.download_media(
                message=data["separate_srt_file_id"],
                file_name=srt_path_temp
            )
        elif subtitle_mode == "BUILT_IN":
            await status_msg.edit_text("Detecting and extracting built-in subtitles...")
            streams = await asyncio.to_thread(ffmpeg_utils.detect_built_in_subtitles, video_path)
            if streams:
                subtitle_path = await asyncio.to_thread(ffmpeg_utils.extract_subtitle, video_path, streams[0]['index'], downloads_dir)
            else:
                await message.reply_text("No built-in subtitles found. Uploading without subtitles.")

        # 4. Upload to YouTube
        await status_msg.edit_text("Uploading to YouTube... This may take a while depending on file size.")
        video_id = await asyncio.to_thread(youtube.upload_video, video_path, title, description, category, privacy)

        # 5. Attach Thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            await status_msg.edit_text("Setting YouTube thumbnail...")
            try:
                await asyncio.to_thread(youtube.set_thumbnail, video_id, thumbnail_path)
            except Exception as e:
                await message.reply_text(f"Warning: Failed to set thumbnail: {e}")

        # 6. Attach Subtitles
        if subtitle_path and os.path.exists(subtitle_path):
            await status_msg.edit_text("Uploading subtitles to YouTube...")
            try:
                await asyncio.to_thread(youtube.upload_caption, video_id, subtitle_path)
            except Exception as e:
                await message.reply_text(f"Warning: Failed to upload captions: {e}")

        yt_link = f"https://youtu.be/{video_id}"
        await status_msg.edit_text(f"**Upload Successful!**\n\nLink: {yt_link}")

    except Exception as e:
        await status_msg.edit_text(f"An error occurred during the process:\n`{str(e)}`")
    finally:
        reset_user_data(user_id)
        # Cleanup files
        for p in [video_path, thumbnail_path, subtitle_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
