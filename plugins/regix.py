import os
import sys
import math
import time as tm # Ubah import time menjadi tm untuk menghindari konflik dengan time.time()
import asyncio
import logging
from .utils import STS
from database import db
from .test import CLIENT, start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters
# from pyropatch.utils import unpack_new_file_id # Pastikan ini diimpor jika digunakan di tempat lain
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
    InputMediaPhoto, # Tambahkan ini untuk album
    InputMediaVideo # Tambahkan ini untuk album
)

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

# --- Tambahan untuk Penanganan Media Group ---
MEDIA_GROUP_CACHE = {}
MEDIA_GROUP_TIMEOUT = 1.5 # Detik. Waktu tunggu untuk mengumpulkan semua bagian album

# --- Akhir Tambahan untuk Penanganan Media Group ---

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    if temp.lock.get(user) and str(temp.lock.get(user)) == "True":
        return await message.answer("Please Wait Until Previous Task Complete", show_alert=True)
    
    sts = STS(frwd_id)
    if not sts.verify():
        await message.answer("Your Are Clicking On My Old Button", show_alert=True)
        return await message.message.delete()
    
    i = sts.get(full=True)
    if i.TO in temp.IS_FRWD_CHAT:
        return await message.answer("In Target Chat A Task Is Progressing. Please Wait Until Task Complete", show_alert=True)
    
    m = await msg_edit(message.message, "Verifying Your Data's, Please Wait.")
    _bot, caption_template, forward_tag, data, protect, button_markup = await sts.get_data(user) # Ubah nama variabel caption dan button untuk menghindari konflik
    
    if not _bot:
        return await msg_edit(m, "You Didn't Added Any Bot. Please Add A Bot Using /settings !", wait=True)
    
    try:
        client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:
        return await m.edit(e)
    
    await msg_edit(m, "Processing...")
    
    try:
        # Cek akses ke chat sumber (FROM)
        # Ambil pesan pertama saja, atau pesan di offset
        await client.get_messages(i.FROM, 1, int(i.skip) if i.skip else 0)
    except Exception as e:
        logger.error(f"Error accessing source chat {i.FROM}: {e}")
        await msg_edit(m, f"Source Chat May Be A Private Channel / Group. Use Userbot (User Must Be Member Over There) Or If Make Your [Bot](t.me/{_bot['username']}) An Admin Over There", retry_btn(frwd_id), True)
        return await stop(client, user)
    
    try:
        # Cek akses ke chat target (TO) dan izin kirim pesan
        k = await client.send_message(i.TO, "Testing")
        await k.delete()
    except Exception as e:
        logger.error(f"Error accessing target chat {i.TO}: {e}")
        await msg_edit(m, f"Please Make Your [UserBot / Bot](t.me/{_bot['username']}) Admin In Target Channel With Full Permissions", retry_btn(frwd_id), True)
        return await stop(client, user)
    
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "🩷 Forwarding Started")
    sts.add(time=True)
    sleep_interval = 1 if _bot['is_bot'] else 10 # Interval tidur antara pesan individual
    await msg_edit(m, "Processing...")
    
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    
    if locked:
        try:
            # Perbaikan: Hapus argumen 'client' yang redundant
            async for message in client.iter_messages(
                chat_id=sts.get('FROM'),
                limit=int(sts.get('limit')),
                offset=int(sts.get('skip')) if sts.get('skip') else 0
            ):
                if await is_cancelled(client, user, m, sts):
                    return

                # Perbarui status setiap 20 pesan
                if sts.get('fetched') % 20 == 0: # Gunakan sts.get('fetched') yang terupdate
                    await edit(m, 'Progressing', 10, sts)
                
                # --- Logika penanganan pesan ---
                if message == "DUPLICATE":
                    sts.add('duplicate')
                    sts.add('fetched') # Tetap hitung sebagai fetched
                    continue
                elif message == "FILTERED":
                    sts.add('filtered')
                    sts.add('fetched') # Tetap hitung sebagai fetched
                    continue
                
                if message.empty or message.service:
                    sts.add('deleted')
                    sts.add('fetched') # Tetap hitung sebagai fetched
                    continue
                
                # Panggil fungsi baru untuk memproses pesan, termasuk album
                await process_message_for_forwarding(
                    client, # bot client
                    message, # message object
                    sts, # STS object
                    protect, # protect content
                    caption_template, # caption template
                    button_markup, # inline buttons
                    _bot['is_bot'], # is bot (for sleep interval)
                    m # message edit object
                )
                
                # Sleep hanya jika bukan bagian dari media group yang sedang dikumpulkan
                # Logika sleep dipindahkan ke dalam process_message_for_forwarding atau send_media_group_after_delay
                # agar tidak mengganggu pengumpulan album
                # Jika Anda tetap ingin ada sleep antar pesan individual yang bukan album, bisa di sini:
                # if not message.media_group_id:
                #     await asyncio.sleep(sleep_interval)
                # --- Akhir logika penanganan pesan ---
                
        except Exception as e:
            logger.error(f"Main forwarding loop error: {e}", exc_info=True)
            await msg_edit(m, f'<b>Error :</b>\n<code>{e}</code>', wait=True)
            if i.TO in temp.IS_FRWD_CHAT:
                temp.IS_FRWD_CHAT.remove(i.TO)
            return await stop(client, user)
        
        # Pastikan tidak ada media group yang tertinggal di cache
        # Ini penting jika iterasi berakhir dan masih ada group yang belum dikirim
        for group_id in list(MEDIA_GROUP_CACHE.keys()): # Iterate over a copy of keys
            if group_id in MEDIA_GROUP_CACHE and MEDIA_GROUP_CACHE[group_id]["task"]:
                MEDIA_GROUP_CACHE[group_id]["task"].cancel() # Batalkan task yang mungkin tertunda
                await send_media_group_after_delay( # Coba kirim segera
                    client,
                    group_id,
                    sts.get('TO'),
                    protect,
                    caption_template, # Kirim template caption
                    button_markup, # Kirim button markup
                    sts,
                    m
                )
        
        if i.TO in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(i.TO)
        await send(client, user, "🎉 Forwarding Completed")
        await edit(m, 'Completed', "completed", sts)
        await stop(client, user)


# --- Fungsi baru untuk memproses pesan (media group atau tunggal) ---
async def process_message_for_forwarding(bot, message_obj, sts_object, protect, caption_template, button_markup, is_bot_client, progress_msg_obj):
    sleep_interval = 1 if is_bot_client else 10 # Interval tidur antara pesan individual
    
    if message_obj.media_group_id:
        group_id = message_obj.media_group_id

        if group_id not in MEDIA_GROUP_CACHE:
            MEDIA_GROUP_CACHE[group_id] = {
                "messages": [],
                "last_seen": tm.time(),
                "task": None,
                "first_message": message_obj # Simpan pesan pertama untuk caption/buttons
            }

        MEDIA_GROUP_CACHE[group_id]["messages"].append(message_obj)
        MEDIA_GROUP_CACHE[group_id]["last_seen"] = tm.time()

        if MEDIA_GROUP_CACHE[group_id]["task"]:
            MEDIA_GROUP_CACHE[group_id]["task"].cancel()

        MEDIA_GROUP_CACHE[group_id]["task"] = asyncio.create_task(
            send_media_group_after_delay(
                bot,
                group_id,
                sts_object.get('TO'),
                protect,
                caption_template,
                button_markup,
                sts_object,
                progress_msg_obj # Kirim objek pesan progress untuk update
            )
        )
        sts_object.add('fetched') # Hitung pesan ini sebagai 'fetched' meskipun belum dikirim
        return # Jangan proses pesan individual sekarang

    # Jika bukan media group, proses pesan individual seperti biasa
    if protect: # Jika forward_tag (protect) adalah True, gunakan forward_messages
        try:
            await forward(bot, [message_obj.id], progress_msg_obj, sts_object, protect) # Kirim sebagai list untuk forward_messages
            sts_object.add('total_files')
            await asyncio.sleep(sleep_interval)
        except FloodWait as e:
            await edit(progress_msg_obj, 'Progressing', e.value, sts_object)
            await asyncio.sleep(e.value)
            await edit(progress_msg_obj, 'Progressing', 10, sts_object)
            await forward(bot, [message_obj.id], progress_msg_obj, sts_object, protect) # Retry
            sts_object.add('total_files')
            await asyncio.sleep(sleep_interval)
        except Exception as e:
            logger.error(f"Error forwarding single message {message_obj.id}: {e}")
            sts_object.add('deleted')
    else: # Jika tidak ada forward_tag, gunakan copy_message atau send_cached_media
        new_caption = custom_caption(message_obj, caption_template)
        details = {
            "msg_id": message_obj.id,
            "media": media(message_obj),
            "caption": new_caption,
            'button': button_markup,
            "protect": protect
        }
        try:
            await copy(bot, details, progress_msg_obj, sts_object)
            sts_object.add('total_files')
            await asyncio.sleep(sleep_interval)
        except FloodWait as e:
            await edit(progress_msg_obj, 'Progressing', e.value, sts_object)
            await asyncio.sleep(e.value)
            await edit(progress_msg_obj, 'Progressing', 10, sts_object)
            await copy(bot, details, progress_msg_obj, sts_object) # Retry
            sts_object.add('total_files')
            await asyncio.sleep(sleep_interval)
        except Exception as e:
            logger.error(f"Error copying single message {message_obj.id}: {e}")
            sts_object.add('deleted')
    
    sts_object.add('fetched') # Hitung pesan ini sebagai 'fetched' setelah diproses

# Fungsi untuk mengirim media group setelah penundaan
async def send_media_group_after_delay(bot, group_id, target_chat_id, protect, caption_template, button_markup, sts_object, progress_msg_obj):
    try:
        await asyncio.sleep(MEDIA_GROUP_TIMEOUT) # Tunggu sebentar untuk memastikan semua bagian terkumpul

        if group_id in MEDIA_GROUP_CACHE:
            group_data = MEDIA_GROUP_CACHE[group_id]
            messages_to_send = group_data["messages"]
            first_message_in_group = group_data["first_message"]

            if not messages_to_send:
                return # Tidak ada pesan untuk dikirim

            # Sortir pesan berdasarkan message_id untuk urutan yang benar
            messages_to_send.sort(key=lambda m: m.id)

            input_media = []
            final_caption = custom_caption(first_message_in_group, caption_template)
            
            # Hanya tambahkan caption dan reply_markup ke media pertama
            # Pyrogram akan menggunakan caption dari item pertama untuk seluruh media group
            first_item = True

            for msg in messages_to_send:
                if msg.photo:
                    input_media.append(InputMediaPhoto(
                        media=msg.photo.file_id,
                        caption=final_caption if first_item else None
                    ))
                elif msg.video:
                    input_media.append(InputMediaVideo(
                        media=msg.video.file_id,
                        caption=final_caption if first_item else None
                    ))
                # TODO: Tambahkan penanganan untuk InputMediaDocument, InputMediaAudio jika diperlukan
                # Contoh:
                # elif msg.document:
                #     input_media.append(InputMediaDocument(media=msg.document.file_id, caption=final_caption if first_item else None))
                # elif msg.audio:
                #     input_media.append(InputMediaAudio(media=msg.audio.file_id, caption=final_caption if first_item else None))
                
                first_item = False # Setelah item pertama, set ke False

            if input_media:
                try:
                    # Kirim sebagai media group
                    sent_messages = await bot.send_media_group(
                        chat_id=target_chat_id,
                        media=input_media,
                        reply_markup=button_markup if button_markup else None, # Tombol dilampirkan ke group
                        # protect_content=protect # Pyrogram send_media_group tidak memiliki protect_content langsung
                                                  # Anda harus mengatur ini di setiap InputMedia jika didukung
                    )
                    # Jika protect_content diperlukan untuk setiap media dalam grup:
                    # Cek dokumentasi Pyrogram, beberapa versi mendukung protect_content di InputMedia
                    # for media_item in input_media:
                    #     media_item.protect_content = protect
                    
                    sts_object.add('total_files', len(input_media)) # Update status dengan jumlah file di group
                    
                    # Update progress bar
                    await edit(progress_msg_obj, 'Progressing', 10, sts_object)

                except FloodWait as e:
                    logger.warning(f"FloodWait on sending media group {group_id}: {e.value} seconds")
                    await edit(progress_msg_obj, 'Progressing', e.value, sts_object)
                    await asyncio.sleep(e.value)
                    await send_media_group_after_delay( # Coba lagi setelah sleep
                        bot, group_id, target_chat_id, protect, caption_template, button_markup, sts_object, progress_msg_obj
                    )
                    return # Penting: Jangan hapus dari cache jika retry
                except Exception as e:
                    logger.error(f"Error sending media group {group_id}: {e}", exc_info=True)
                    # Jika terjadi error saat mengirim group, hitung sebagai deleted
                    sts_object.add('deleted', len(input_media))
                    await edit(progress_msg_obj, 'Progressing', 10, sts_object) # Update progress

            if group_id in MEDIA_GROUP_CACHE: # Hapus dari cache setelah dikirim (atau jika ada error selain FloodWait)
                del MEDIA_GROUP_CACHE[group_id]

    except asyncio.CancelledError:
        # Task dibatalkan karena ada pesan baru masuk ke group yang sama atau proses utama dihentikan
        logger.info(f"Media group task {group_id} cancelled.")
        if group_id in MEDIA_GROUP_CACHE:
            # Jika dibatalkan karena ada pesan baru, jangan hapus dari cache
            # Jika dibatalkan karena proses utama selesai/dihentikan, biarkan cleanup di main loop yang menangani
            pass
    except Exception as e:
        logger.error(f"Unexpected error in send_media_group_after_delay for group {group_id}: {e}", exc_info=True)
        # Pastikan group dihapus dari cache jika terjadi error fatal
        if group_id in MEDIA_GROUP_CACHE:
            del MEDIA_GROUP_CACHE[group_id]


# --- Fungsi copy (untuk pesan tunggal tanpa forward tag) ---
async def copy(bot, msg_details, m, sts):
    try:
        # Prioritaskan send_cached_media jika ada file_id media
        if msg_details.get("media") and not msg_details.get("caption") and not msg_details.get("button"):
            await bot.send_cached_media(
                chat_id=sts.get('TO'),
                file_id=msg_details.get("media"),
                protect_content=msg_details.get("protect")
            )
        else:
            await bot.copy_message(
                chat_id=sts.get('TO'),
                from_chat_id=sts.get('FROM'),
                caption=msg_details.get("caption"),
                message_id=msg_details.get("msg_id"),
                reply_markup=msg_details.get('button'),
                protect_content=msg_details.get("protect")
            )
    except FloodWait as e:
        logger.warning(f"FloodWait on copy message {msg_details.get('msg_id')}: {e.value} seconds")
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await edit(m, 'Progressing', 10, sts)
        await copy(bot, msg_details, m, sts) # Retry
    except Exception as e:
        logger.error(f"Error in copy message {msg_details.get('msg_id')}: {e}", exc_info=True)
        sts.add('deleted')

# --- Fungsi forward (untuk pesan tunggal dengan forward tag) ---
async def forward(bot, msg_ids, m, sts, protect): # msg_ids sekarang adalah list
    try:
        await bot.forward_messages(
            chat_id=sts.get('TO'),
            from_chat_id=sts.get('FROM'),
            protect_content=protect,
            message_ids=msg_ids # message_ids harus berupa list
        )
    except FloodWait as e:
        logger.warning(f"FloodWait on forward messages {msg_ids}: {e.value} seconds")
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await edit(m, 'Progressing', 10, sts)
        await forward(bot, msg_ids, m, sts, protect) # Retry
    except Exception as e:
        logger.error(f"Error in forward messages {msg_ids}: {e}", exc_info=True)
        sts.add('deleted', len(msg_ids)) # Tambahkan jumlah pesan yang gagal

PROGRESS = """
📈 Percetage : {0} %

♻️ Fetched : {1}

🔥 Forwarded : {2}

🫠 Remaining : {3}

📊 Status : {4}

⏳️ ETA : {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass
    except FloodWait as e:
        if wait:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, button, wait)
        logger.warning(f"FloodWait on msg_edit: {e.value} seconds")
        await asyncio.sleep(e.value)
        return await msg_edit(msg, text, button) # Coba lagi tanpa 'wait' khusus

async def edit(msg, title, status_val, sts): # Ubah status menjadi status_val untuk menghindari konflik nama
    i = sts.get(full=True)
    status_text = 'Forwarding' if status_val == 10 else f"Sleeping {status_val} s" if str(status_val).isnumeric() else status_val
    
    # Menghitung persentase dengan aman
    percentage = 0
    if i.total > 0:
        percentage = "{:.0f}".format(float(i.fetched) * 100 / float(i.total))
    else:
        percentage = "0" # Jika total adalah 0

    now = tm.time() # Gunakan tm.time()
    diff = int(now - i.start)
    
    speed = 0
    if diff > 0:
        speed = sts.divide(i.fetched, diff)
    
    elapsed_time = round(diff) * 1000
    
    time_to_completion = 0
    if speed > 0:
        time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
    
    estimated_total_time = elapsed_time + time_to_completion

    progress = "▰{0}{1}".format(
        ''.join(["▰" for _ in range(math.floor(int(percentage) / 10))]),
        ''.join(["▱" for _ in range(10 - math.floor(int(percentage) / 10))])
    )
    
    # Data untuk tombol status
    button_data = f'fwrdstatus#{status_text}#{estimated_total_time}#{percentage}#{i.id}'
    button = [[InlineKeyboardButton(title, button_data)]]
    
    estimated_total_time_str = TimeFormatter(milliseconds=estimated_total_time)
    estimated_total_time_str = estimated_total_time_str if estimated_total_time_str != '' else '0 s'

    text_to_send = TEXT.format(
        i.fetched, i.total_files, i.duplicate, i.deleted, i.skip,
        status_text, percentage, estimated_total_time_str, progress
    )
    
    if status_val in ["cancelled", "completed"]:
        button.append(
            [InlineKeyboardButton('📢 Updates', url='https://t.me/learningbots79'),
             InlineKeyboardButton('💬 Support', url='https://t.me/learning_bots')]
        )
    else:
        button.append([InlineKeyboardButton('✖️ Cancel ✖️', 'terminate_frwd')])
    
    await msg_edit(msg, text_to_send, InlineKeyboardMarkup(button))

async def is_cancelled(client_obj, user, msg, sts): # Ganti client menjadi client_obj
    if temp.CANCEL.get(user) == True:
        if sts.TO in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(sts.TO)
        await edit(msg, "Cancelled", "completed", sts)
        await send(client_obj, user, "❌ Forwarding Process Cancelled") # Gunakan client_obj
        await stop(client_obj, user) # Gunakan client_obj
        
        # Batalkan semua task media group yang tertunda untuk user ini
        for group_id in list(MEDIA_GROUP_CACHE.keys()):
            if group_id in MEDIA_GROUP_CACHE and MEDIA_GROUP_CACHE[group_id]["task"]:
                MEDIA_GROUP_CACHE[group_id]["task"].cancel()
                del MEDIA_GROUP_CACHE[group_id]
        
        return True
    return False

async def stop(client_obj, user): # Ganti client menjadi client_obj
    try:
        await client_obj.stop() # Gunakan client_obj
    except Exception as e:
        logger.error(f"Error stopping client: {e}")
        pass
    await db.rmve_frwd(user)
    temp.forwardings -= 1
    temp.lock[user] = False

async def send(bot_obj, user, text): # Ganti bot menjadi bot_obj
    try:
        await bot_obj.send_message(user, text=text) # Gunakan bot_obj
    except Exception as e:
        logger.error(f"Error sending message to user {user}: {e}")
        pass

def custom_caption(msg, caption_template): # Ganti caption menjadi caption_template
    if msg.media:
        if (msg.video or msg.document or msg.audio or msg.photo):
            media_obj = getattr(msg, msg.media.value, None)
            if media_obj:
                file_name = getattr(media_obj, 'file_name', '')
                file_size = getattr(media_obj, 'file_size', '')
                fcaption = getattr(msg, 'caption', '')
                if fcaption:
                    fcaption = fcaption.html
                if caption_template:
                    return caption_template.format(filename=file_name, size=get_size(file_size), caption=fcaption)
                return fcaption
    return None

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def media(msg):
    if msg.media:
        media_obj = getattr(msg, msg.media.value, None)
        if media_obj:
            return getattr(media_obj, 'file_id', None)
    return None

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "") + \
          ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ Retry ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot_client, m): # Ganti bot menjadi bot_client
    user_id = m.from_user.id
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True
    await m.answer("Forwarding Cancelled !", show_alert=True)
    # Media group tasks akan dibatalkan oleh is_cancelled jika user mengklik cancel

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot_client, msg): # Ganti bot menjadi bot_client
    _, status_text, est_time_ms, percentage_str, frwd_id = msg.data.split("#") # Ubah nama variabel
    sts = STS(frwd_id)
    
    fetched = 0
    forwarded = 0
    remaining = 0
    
    if not sts.verify():
        # Jika STS tidak valid, mungkin tugas sudah selesai atau dibatalkan sebelumnya
        # Gunakan nilai default atau beritahu user bahwa status tidak ditemukan
        pass # Biarkan 0 seperti inisialisasi di atas
    else:
        fetched = sts.get('fetched')
        forwarded = sts.get('total_files')
        # Sisa pesan yang belum diproses dari total yang diminta (limit)
        remaining = max(0, sts.get('total') - fetched) 
        
    est_time_str = TimeFormatter(milliseconds=int(est_time_ms)) # Pastikan est_time_ms adalah int
    est_time_str = est_time_str if (est_time_str != '' or status_text not in ['completed', 'cancelled']) else '0 s'
    
    return await msg.answer(PROGRESS.format(percentage_str, fetched, forwarded, remaining, status_text, est_time_str), show_alert=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot_client, update): # Ganti bot menjadi bot_client
    await update.answer()
    await update.message.delete()
    if update.message.reply_to_message: # Tambahkan cek jika reply_to_message ada
        await update.message.reply_to_message.delete()
