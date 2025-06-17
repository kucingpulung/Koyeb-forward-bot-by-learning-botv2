import os
from config import Config

class Translation(object):
  START_TXT = """Hai {}

➻ Saya adalah Bot Auto Forward canggih

➻ Saya bisa meneruskan semua pesan dari satu channel ke channel lain

➻ Klik tombol Bantuan untuk tahu lebih lanjut tentang saya

<b>Bot ini dibuat oleh @Madflix_Bots</b>"""


  HELP_TXT = """<b><u>🛠️ Bantuan</b></u>

<b><u>📚 Perintah yang Tersedia :</u></b>
⏣ __/start - Cek apakah saya aktif__  
⏣ __/forward - Teruskan pesan__  
⏣ __/unequify - Hapus pesan duplikat di channel__  
⏣ __/settings - Atur konfigurasi Anda__  
⏣ __/reset - Atur ulang pengaturan Anda__

<b><u>💢 Fitur :</b></u>
► __Teruskan pesan dari channel publik ke channel Anda tanpa perlu admin. Jika channel privat, perlu izin admin.__  
► __Teruskan pesan dari channel privat ke channel Anda menggunakan userbot (Userbot harus menjadi anggota di sana)__  
► __Caption khusus__  
► __Tombol khusus__  
► __Mendukung obrolan terbatas__  
► __Lewati pesan duplikat__  
► __Filter jenis pesan__  
► __Lewati pesan berdasarkan ekstensi, kata kunci, dan ukuran__
"""
  
  HOW_USE_TXT = """<b><u>⚠️ Sebelum Meneruskan :</b></u>
  
► __Tambahkan Bot atau Userbot terlebih dahulu__  
► __Tambahkan minimal satu ke channel (Bot/Userbot Anda harus menjadi admin di sana)__  
► __Anda bisa menambahkan obrolan atau bot melalui perintah /settings__  
► __Jika **From Channel** bersifat privat, maka userbot Anda harus menjadi anggota atau bot Anda harus admin di sana juga__  
► __Lalu gunakan perintah /forward untuk meneruskan pesan__"""
  
  ABOUT_TXT = """<b>🤖 Nama Saya :</b> {}
<b>📝 Bahasa Pemrograman :</b> <a href='https://python.org'>Python 3</a>
<b>📚 Library :</b> <a href='https://pyrogram.org'>Pyrogram 2.0</a>
<b>🚀 Server :</b> <a href='https://heroku.com'>Heroku</a>
<b>📢 Channel :</b> <a href='https://t.me/Madflix_Bots'>Madflix Botz</a>
<b>🧑‍💻 Developer :</b> <a href='https://t.me/CallAdminRobot'>Jishu Developer</a>

<b>♻️ Bot Ini Dibuat Oleh :</b> @Madflix_Bots"""
  
  STATUS_TXT = """<b><u>Status Bot</u></b>
  
<b>👱 Total Pengguna :</b> <code>{}</code>

<b>🤖 Total Bot :</b> <code>{}</code>

<b>🔃 Penerusan :</b> <code>{}</code>
"""
  
  FROM_MSG = "<b><u>Setel Chat Sumber</u></b>\n\nTeruskan pesan terakhir atau tautan pesan terakhir dari chat sumber.\n/cancel - Untuk membatalkan proses ini"
  TO_MSG = "<b><u>Pilih Chat Tujuan</u></b>\n\nPilih chat tujuan Anda dari tombol yang tersedia.\n/cancel - Untuk membatalkan proses ini"
  SKIP_MSG = "<b><u>Atur Jumlah Pesan yang Dilewati</u></b>\n\nLewati pesan sebanyak angka yang Anda masukkan, sisanya akan diteruskan.\nLewati default = <code>0</code>\n<code>cth: Masukkan 0 = tidak ada yang dilewati\nMasukkan 5 = 5 pesan dilewati</code>\n/cancel - Untuk membatalkan proses ini"
  CANCEL = "Proses berhasil dibatalkan!"
  BOT_DETAILS = "<b><u>📄 Detail Bot</u></b>\n\n<b>➣ Nama :</b> <code>{}</code>\n<b>➣ Bot ID :</b> <code>{}</code>\n<b>➣ Username :</b> @{}"
  USER_DETAILS = "<b><u>📄 Detail UserBot</u></b>\n\n<b>➣ Nama :</b> <code>{}</code>\n<b>➣ User ID :</b> <code>{}</code>\n<b>➣ Username :</b> @{}"  
         
  TEXT = """<b><u>Status Penerusan</u></b>
  
<b>🕵 Pesan Diambil :</b> <code>{}</code>

<b>✅ Berhasil Diteruskan :</b> <code>{}</code>

<b>👥 Pesan Duplikat :</b> <code>{}</code>

<b>🗑 Pesan Dihapus :</b> <code>{}</code>

<b>🪆 Pesan Dilewati :</b> <code>{}</code>

<b>🔁 Pesan Difilter :</b> <code>{}</code>

<b>📊 Status Saat Ini :</b> <code>{}</code>

<b>🔥 Persentase :</b> <code>{}</code> %

{}
"""

  TEXT1 = """<b><u>Status Setelah Diteruskan</u></b>

<b>🕵 Pesan Diambil :</b> <code>{}</code>

<b>✅ Berhasil Diteruskan :</b> <code>{}</code>

<b>👥 Pesan Duplikat :</b> <code>{}</code>

<b>🗑 Pesan Dihapus :</b> <code>{}</code>

<b>🪆 Dilewati :</b> <code>{}</code>

<b>📊 Statistik :</b> <code>{}</code>

<b>⏳ Progres :</b> <code>{}</code>

<b>⏰ Perkiraan Waktu :</b> <code>{}</code>

{}"""

  DUPLICATE_TEXT = """<b><u>Status Pembersihan Duplikat</u></b>

<b>🕵 File Diambil :</b> <code>{}</code>

<b>👥 Duplikat Dihapus :</b> <code>{}</code>

{}
"""
  DOUBLE_CHECK = """<b><u>Pemeriksaan Ganda</u></b>
  
Sebelum meneruskan pesan, klik tombol Ya hanya jika semua berikut ini sudah dicek:

<b>★ Bot Anda :</b> [{botname}](t.me/{botuname})  
<b>★ Dari Channel :</b> <code>{from_chat}</code>  
<b>★ Ke Channel :</b> <code>{to_chat}</code>  
<b>★ Lewati Pesan :</b> <code>{skip}</code>

<i>° [{botname}](t.me/{botuname}) harus menjadi admin di <b>Chat Tujuan</b></i> (<code>{to_chat}</code>)  
<i>° Jika <b>Chat Sumber</b> bersifat privat, maka userbot Anda harus menjadi anggota atau bot harus admin juga</i>

<b>Jika semua sudah dicek, silakan klik tombol Ya</b>"""
