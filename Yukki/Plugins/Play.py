import requests
from Yukki.Utilities.spotify import get_spotify_url, getsp_album_info, getsp_artist_info, getsp_playlist_info, getsp_track_info
from Yukki.Plugins.custom.func import mplay_stream
from Yukki.Utilities.resso import get_resso_album, get_resso_artist, get_resso_playlist, get_resso_track, get_resso_url
from Yukki.Plugins.Resso import resso_buttons, resso_play
from Yukki.Plugins.Spotify import spotify_buttons, spotify_play
import asyncio
from os import path

from pyrogram import filters
from pyrogram.types import (InlineKeyboardMarkup, InputMediaPhoto, Message,
                            Voice)
from youtube_search import YoutubeSearch

import Yukki
from Yukki import (BOT_USERNAME, DURATION_LIMIT, DURATION_LIMIT_MIN,
                   MUSIC_BOT_NAME, app, db_mem)
from Yukki.Core.PyTgCalls.Converter import convert
from Yukki.Core.PyTgCalls.Downloader import download
from Yukki.Core.PyTgCalls.Tgdownloader import telegram_download
from Yukki.Database import (get_active_video_chats, get_video_limit,
                            is_active_video_chat)
from Yukki.Decorators.assistant import AssistantAdd
from Yukki.Decorators.checker import checker
from Yukki.Decorators.logger import logging
from Yukki.Decorators.permission import PermissionCheck
from Yukki.Inline import (livestream_markup, playlist_markup, search_markup,
                          search_markup2, url_markup, url_markup2)
from Yukki.Utilities.changers import seconds_to_min, time_to_seconds
from Yukki.Utilities.chat import specialfont_to_normal
from Yukki.Utilities.stream import start_stream, start_stream_audio
from Yukki.Utilities.theme import check_theme
from Yukki.Utilities.thumbnails import gen_thumb
from Yukki.Utilities.url import get_url
from Yukki.Utilities.videostream import start_stream_video
from Yukki.Utilities.youtube import (get_yt_info_id, get_yt_info_query,
                                     get_yt_info_query_slider)
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram.errors import UserNotParticipant

loop = asyncio.get_event_loop()

JOIN_ASAP = f"🙋‍♂️ hai, Anda Harus Bergabung dengan Saluran Telegram @szteambots Untuk Menggunakan BOT Ini. Jadi, Silakan Bergabung & Coba Lagi. Terima kasih 🤝"

FSUBB = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton(text="Sz Team Bots <sz/>", url=f"https://t.me/synxupdate") 
        ]]
    )


@app.on_message(
    filters.command(["play", f"play@{BOT_USERNAME}"]) & filters.group
)
@checker
@logging
@PermissionCheck
@AssistantAdd
async def play(_, message: Message):
    await message.delete()
    try:
        await message._client.get_chat_member(int("-1001616236548"), message.from_user.id)
    except UserNotParticipant:
        await message.reply_text(
        text=JOIN_ASAP, disable_web_page_preview=True, reply_markup=FSUBB
    )
        return 
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"    
    if message.chat.id not in db_mem:
        db_mem[message.chat.id] = {}
    if message.sender_chat:
        return await message.reply_text(
            "You're an __Anonymous Admin__ in this Chat Group!\nRevert back to User Account From Admin Rights."
        )
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    video = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )
    url = get_url(message)
    if audio:
        mystic = await message.reply_text(
            "Processing Audio... Please Wait!"
        )
        if audio.file_size > 1073741824:
            return await mystic.edit_text(
                "Audio File Size Should Be Less Than 150 mb"
            )
        duration_min = seconds_to_min(audio.duration)
        duration_sec = audio.duration
        if (audio.duration) > DURATION_LIMIT:
            return await mystic.edit_text(
                f"**Duration Limit Exceeded**\n\n**Allowed Duration: **{DURATION_LIMIT_MIN} minute(s)\n**Received Duration:** {duration_min} minute(s)"
            )
        file_name = (
            audio.file_unique_id
            + "."
            + (
                (audio.file_name.split(".")[-1])
                if (not isinstance(audio, Voice))
                else "ogg"
            )
        )
        file_name = path.join(path.realpath("downloads"), file_name)
        file = await convert(
            (await message.reply_to_message.download(file_name))
            if (not path.isfile(file_name))
            else file_name,
        )
        return await start_stream_audio(
            message,
            file,
            "smex1",
            "Given Audio Via Telegram",
            duration_min,
            duration_sec,
            mystic,
        )
    elif video:
        limit = await get_video_limit(141414)
        if not limit:
            return await message.reply_text(
                "**No Limit Defined for Video Calls**\n\nSet a Limit for Number of Maximum Video Calls allowed on Bot by /set_video_limit [Sudo Users Only]"
            )
        count = len(await get_active_video_chats())
        if int(count) == int(limit):
            if await is_active_video_chat(message.chat.id):
                pass
            else:
                return await message.reply_text(
                    "Sorry! Bot only allows limited number of video calls due to CPU overload issues. Many other chats are using video call right now. Try switching to audio or try again later"
                )
        mystic = await message.reply_text(
            "Processing Video... Please Wait!"
        )
        file = await telegram_download(message, mystic)
        return await start_stream_video(
            message,
            file,
            "Given Video Via Telegram",
            mystic,
        )
    elif url:
        if "spotify.com" in url:
            return await message.reply_text("Use /spotify for spotify links")
        
        if "resso.com" in url:            
            return await message.reply_text("Use /resso for resso links")
        
        mystic = await message.reply_text("Processing URL... Please Wait!")
        if not message.reply_to_message:
            query = message.text.split(None, 1)[1]
        else:
            query = message.reply_to_message.text
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
            views, 
            channel
        ) = get_yt_info_query(query)
        await mystic.delete()
        buttons = url_markup2(videoid, duration_min, message.from_user.id)
        return await message.reply_photo(
            photo=thumb,
            caption=f"🏷 **Name:**{title}\n**⏱Duration**: {duration_min} Mins\n🎧 **Request by:**{mention}\n\n[Get  Information](https://t.me/{BOT_USERNAME}?start=info_{videoid})",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        if len(message.command) < 2:
            buttons = playlist_markup(
                message.from_user.first_name, message.from_user.id, "abcd"
            )
            await message.reply_text(
                    "**Usage:** /play [Music Name or Youtube Link or Reply to Audio]\n\nIf you want to play Playlists! Select the one from Below.",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return
        what = "Query Given"
        await LOG_CHAT(message, what)
        mystic = await message.reply_text("**🔎 Searching**")
        query = message.text.split(None, 1)[1]
        user_id = message.from_user.id
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query(query)
        a = VideosSearch(query, limit=5)
        result = (a.result()).get("result")
        title1 = (result[0]["title"])
        duration1 = (result[0]["duration"])
        title2 = (result[1]["title"])
        duration2 = (result[1]["duration"])      
        title3 = (result[2]["title"])
        duration3 = (result[2]["duration"])
        title4 = (result[3]["title"])
        duration4 = (result[3]["duration"])
        title5 = (result[4]["title"])
        duration5 = (result[4]["duration"])
        ID1 = (result[0]["id"])
        ID2 = (result[1]["id"])
        ID3 = (result[2]["id"])
        ID4 = (result[3]["id"])
        ID5 = (result[4]["id"])
        buttons = search_markup(ID1, ID2, ID3, ID4, ID5, duration1, duration2, duration3, duration4, duration5, user_id, query)
        return await mystic.edit(
            f"**🎵 Choose The Result :**\n\n1️⃣ <b>[{title1[:25]}](https://www.youtube.com/watch?v={ID1})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID1})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n2️⃣ <b>[{title2[:25]}](https://www.youtube.com/watch?v={ID2})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID2})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n3️⃣ <b>[{title3[:25]}](https://www.youtube.com/watch?v={ID3})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID3})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n4️⃣ <b>[{title4[:25]}](https://www.youtube.com/watch?v={ID4})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID4})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n5️⃣ <b>[{title5[:25]}](https://www.youtube.com/watch?v={ID5})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID5})</u>\n └ ⚡ __Powered by {BOT_NAME}__",    
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )


@app.on_callback_query(filters.regex(pattern=r"MusicStream"))
async def Music_Stream(_, CallbackQuery):
    if CallbackQuery.message.chat.id not in db_mem:
        db_mem[CallbackQuery.message.chat.id] = {}
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    chat_id = CallbackQuery.message.chat.id
    chat_title = CallbackQuery.message.chat.title
    videoid, duration, user_id = callback_request.split("|")
    if str(duration) == "None":
        buttons = livestream_markup("720", videoid, duration, user_id)
        return await CallbackQuery.edit_message_text(
            "**Live Stream Detected**\n\nWant to play live stream? This will stop the current playing musics(if any) and will start streaming live video.",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "This is not for you! Search You Own Song.", show_alert=True
        )
    await CallbackQuery.message.delete()
    (
        title,
        duration_min,
        duration_sec,
        thumbnail,
        views,
        channel
    ) = get_yt_info_id(videoid)
    if duration_sec > DURATION_LIMIT:
        return await CallbackQuery.message.reply_text(
            f"**Duration Limit Exceeded**\n\n**Allowed Duration: **{DURATION_LIMIT_MIN} minute(s)\n**Received Duration:** {duration_min} minute(s)"
        )
    await CallbackQuery.answer(f"Processing:- {title[:20]}", show_alert=True)
    mystic = await CallbackQuery.message.reply_text(
        f"**{MUSIC_BOT_NAME} Downloader**\n\n**Title:** {title[:50]}\n\n0% ▓▓▓▓▓▓▓▓▓▓▓▓ 100%"
    )
    downloaded_file = await loop.run_in_executor(
        None, download, videoid, mystic, title
    )
    raw_path = await convert(downloaded_file)
    theme = await check_theme(chat_id)
    chat_title = await specialfont_to_normal(chat_title)
    thumb = await gen_thumb(
                        thumbnail, title, CallbackQuery.from_user.id, "NOW PLAYING", views, duration_min, channel
                    )
    if chat_id not in db_mem:
        db_mem[chat_id] = {}
    await start_stream(
        CallbackQuery,
        raw_path,
        videoid,
        thumb,
        title,
        duration_min,
        duration_sec,
        mystic,
    )


@app.on_callback_query(filters.regex(pattern=r"Search"))
async def search_query_more(_, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "Search Your Own Music. You're not allowed to use this button.",
            show_alert=True,
        )
    await CallbackQuery.answer("Searching More Results")
    results = YoutubeSearch(query, max_results=5).to_dict()
    med = f"1️⃣ <b>{results[0]['title']}</b>\n └ 💡 [More information](https://t.me/{BOT_USERNAME}?start=info_{results[0]['id']})\n\n2️⃣ <b>{results[1]['title']}</b>\n └ 💡 [More information](https://t.me/{BOT_USERNAME}?start=info_{results[1]['id']})\n\n3️⃣ <b>{results[2]['title']}</b>\n └ 💡 [More information](https://t.me/{BOT_USERNAME}?start=info_{results[3]['id']})\n\n4️⃣ <b>{results[3]['title']}</b>\n └ 💡 [More information](https://t.me/{BOT_USERNAME}?start=info_{results[3]['id']})\n\n5️⃣ <b>{results[4]['title']}</b>\n └ 💡 [More information](https://t.me/{BOT_USERNAME}?start=info_{results[4]['id']})"

    buttons = search_markup(
        results[0]["id"],
        results[1]["id"],
        results[2]["id"],
        results[3]["id"],
        results[4]["id"],
        results[0]["duration"],
        results[1]["duration"],
        results[2]["duration"],
        results[3]["duration"],
        results[4]["duration"],
        user_id,
        query,
    )
    return await CallbackQuery.edit_message_text(med, reply_markup=InlineKeyboardMarkup(buttons)
    )


@app.on_callback_query(filters.regex(pattern=r"popat"))
async def popat(_, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    userid = CallbackQuery.from_user.id
    id, query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "Ini bukan untukmu! Cari streaming mu sendiri", show_alert=True
        )
    i=int(id)
    query = str(query)
    try:
        a = VideosSearch(query, limit=10)
        result = (a.result()).get("result")
        title1 = (result[0]["title"])
        duration1 = (result[0]["duration"])
        title2 = (result[1]["title"])
        duration2 = (result[1]["duration"])      
        title3 = (result[2]["title"])
        duration3 = (result[2]["duration"])
        title4 = (result[3]["title"])
        duration4 = (result[3]["duration"])
        title5 = (result[4]["title"])
        duration5 = (result[4]["duration"])
        title6 = (result[5]["title"])
        duration6 = (result[5]["duration"])
        title7 = (result[6]["title"])
        duration7 = (result[6]["duration"])      
        title8 = (result[7]["title"])
        duration8 = (result[7]["duration"])
        title9 = (result[8]["title"])
        duration9 = (result[8]["duration"])
        title10 = (result[9]["title"])
        duration10 = (result[9]["duration"])
        ID1 = (result[0]["id"])
        ID2 = (result[1]["id"])
        ID3 = (result[2]["id"])
        ID4 = (result[3]["id"])
        ID5 = (result[4]["id"])
        ID6 = (result[5]["id"])
        ID7 = (result[6]["id"])
        ID8 = (result[7]["id"])
        ID9 = (result[8]["id"])
        ID10 = (result[9]["id"])
    except Exception as e:
        n = await mystic.edit(f"😕 Song not found.\n\n» Try searching with a clearer title, or add the artist's name as well..")
        await asyncio.sleep(10)
        await message.delete()
        await n.delete()
        return
    if i == 1:
        buttons = search_markup2(ID6, ID7, ID8, ID9, ID10, duration6, duration7, duration8, duration9, duration10, user_id, query)
        await CallbackQuery.edit_message_text(
            f"**🎵 Choose The Result :**\n\n6️⃣ <b>[{title6[:25]}](https://www.youtube.com/watch?v={ID6})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID6})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n️️7️⃣ <b>[{title7[:25]}](https://www.youtube.com/watch?v={ID7})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID7})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n8️⃣ <b>[{title8[:25]}](https://www.youtube.com/watch?v={ID8})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID8})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n9️⃣ <b>[{title9[:25]}](https://www.youtube.com/watch?v={ID9})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID9})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n🔟 <b>[{title10[:25]}](https://www.youtube.com/watch?v={ID10})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID10})</u>\n └ ⚡ __Powered by {BOT_NAME}__",    
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        return
    if i == 2:
        buttons = search_markup(ID1, ID2, ID3, ID4, ID5, duration1, duration2, duration3, duration4, duration5, user_id, query)
        await CallbackQuery.edit_message_text(
            f"**🎵 Choose The Result :**\n\n1️⃣ <b>[{title1[:25]}](https://www.youtube.com/watch?v={ID1})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID1})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n2️⃣ <b>[{title2[:25]}](https://www.youtube.com/watch?v={ID2})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID2})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n3️⃣ <b>[{title3[:25]}](https://www.youtube.com/watch?v={ID3})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID3})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n4️⃣ <b>[{title4[:25]}](https://www.youtube.com/watch?v={ID4})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID4})</u>\n └ ⚡ __Powered by {BOT_NAME}__\n\n5️⃣ <b>[{title5[:25]}](https://www.youtube.com/watch?v={ID5})</b>\n ├ 💡 <u>[More Information](https://t.me/{BOT_USERNAME}?start=info_{ID5})</u>\n └ ⚡ __Powered by {BOT_NAME}__",    
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview = True
        )
        return


@app.on_callback_query(filters.regex(pattern=r"slider"))
async def slider_query_results(_, CallbackQuery):
    mention = f"[{CallbackQuery.from_user.first_name}](tg://user?id={CallbackQuery.from_user.id})"
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    what, type, query, user_id = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        return await CallbackQuery.answer(
            "Search Your Own Music. You're not allowed to use this button.",
            show_alert=True,
        )
    what = str(what)
    type = int(type)
    if what == "F":
        if type == 9:
            query_type = 0
        else:
            query_type = int(type + 1)
        await CallbackQuery.answer("Getting Next Result", show_alert=True)
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query_slider(query, query_type)
        buttons = url_markup(
            videoid, duration_min, user_id, query, query_type
        )
        med = InputMediaPhoto(
            media=thumb,
            caption=f"🏷 **Name:**{title}\n**⏱ Duration**: {duration_min} Mins\n🎧 **Request by:**{mention}\n\n[Get  Information](https://t.me/{BOT_USERNAME}?start=info_{videoid})",
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
    if what == "B":
        if type == 0:
            query_type = 9
        else:
            query_type = int(type - 1)
        await CallbackQuery.answer("Getting Previous Result", show_alert=True)
        (
            title,
            duration_min,
            duration_sec,
            thumb,
            videoid,
        ) = get_yt_info_query_slider(query, query_type)
        buttons = url_markup(
            videoid, duration_min, user_id, query, query_type
        )
        med = InputMediaPhoto(
            media=thumb,
            caption=f"🏷 **Name:**{title}\n**⏱ Duration**: {duration_min} Mins\n🎧 **Request by:**{mention}\n\n[Get  Information](https://t.me/{BOT_USERNAME}?start=info_{videoid})",
        )
        return await CallbackQuery.edit_message_media(
            media=med, reply_markup=InlineKeyboardMarkup(buttons)
        )
