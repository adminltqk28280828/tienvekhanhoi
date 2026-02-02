import telebot
from telebot import types
import datetime
import json
import os

# --- CẤU HÌNH ---
API_TOKEN = '8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw'
ADMIN_ID = 6684980246
ADMIN_NAME = "Quốc Khánh"

bot = telebot.TeleBot(API_TOKEN)
USER_FILE = "users.txt"
LOG_FILE = "sent_messages.json"

# --- HÀM HỖ TRỢ ---
def save_user(user_id):
    user_id = str(user_id)
    try:
        with open(USER_FILE, "a+") as f:
            f.seek(0)
            users = f.read().splitlines()
            if user_id not in users:
                f.write(user_id + "\n")
    except Exception as e:
        print(f"Lỗi lưu user: {e}")

def get_sent_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []

def save_sent_log(log_data):
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f)

# --- XỬ LÝ LỆNH ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, f"🌟 Chào mừng bạn đến với Bot của {ADMIN_NAME} Media!")

# 1. Tính năng mới: Xem danh sách người dùng
@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id == ADMIN_ID:
        try:
            if not os.path.exists(USER_FILE):
                bot.reply_to(message, "❌ Chưa có dữ liệu người dùng.")
                return

            with open(USER_FILE, "r") as f:
                users = f.read().splitlines()
            
            if not users:
                bot.reply_to(message, "❌ Danh sách người dùng trống.")
                return

            # Tạo nội dung danh sách
            user_list_text = f"📊 **DANH SÁCH NGƯỜI DÙNG ({len(users)})**\n\n"
            for i, user_id in enumerate(users, 1):
                user_list_text += f"{i}. ID: `{user_id}`\n"
            
            # Nếu danh sách quá dài, Telegram sẽ không cho gửi 1 tin nhắn. 
            # Đoạn này xử lý gửi nhiều tin nếu cần.
            if len(user_list_text) > 4000:
                bot.reply_to(message, f"📊 Tổng số người dùng: {len(users)}. Danh sách quá dài để hiển thị hết.")
            else:
                bot.reply_to(message, user_list_text, parse_mode="Markdown")
                
        except Exception as e:
            bot.reply_to(message, f"❌ Lỗi khi đọc danh sách: {e}")
    else:
        bot.reply_to(message, "🚫 Bạn không có quyền Admin.")

# 2. Gửi thông báo cho mọi người
@bot.message_handler(commands=['send'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace('/send', '').strip()
        if not msg_text:
            bot.reply_to(message, "⚠️ Nhập: `/send Nội dung` ", parse_mode="Markdown")
            return

        try:
            with open(USER_FILE, "r") as f:
                users = f.read().splitlines()
            
            sent_history = []
            success = 0
            for user in users:
                try:
                    sent_msg = bot.send_message(user, msg_text)
                    sent_history.append({"chat_id": user, "message_id": sent_msg.message_id})
                    success += 1
                except: continue
            
            save_sent_log(sent_history)
            bot.send_message(ADMIN_ID, f"✅ Đã gửi tới {success} người.")
        except FileNotFoundError:
            bot.send_message(ADMIN_ID, "❌ Chưa có dữ liệu người dùng.")
    else:
        bot.reply_to(message, "🚫 Bạn không có quyền Admin.")

# 3. Tạo bảng Bill chuyên nghiệp và gửi cho mọi người
@bot.message_handler(commands=['bill'])
def create_bill(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 Bạn không có quyền Admin.")
        return

    try:
        input_data = message.text.replace('/bill', '').strip()
        if not input_data:
            guide = "📝 **Mẫu nhập:**\n`/bill UID | DIE | Tên | Ghi chú | Giá | Tiến trình | Thời gian sống`"
            bot.reply_to(message, guide, parse_mode="Markdown")
            return

        parts = [p.strip() for p in input_data.split('|')]
        uid, status, name, note, price, progress, lifetime = parts
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_icon = "❌" if "DIE" in status.upper() else "✅"
        header = f"{status_icon} {status} rồi sếp ơi {ADMIN_NAME}!" if "DIE" in status.upper() else f"✅ NGON rồi sếp ơi {ADMIN_NAME}!"

        html_text = (
            f"<b>{header}</b>\n\n"
            f"UID {uid} - {status.upper()} {status_icon}\n\n"
            f"👤 <b>Tên:</b> {name}\n"
            f"📝 <b>Ghi chú:</b> {note}\n"
            f"💵 <b>Giá:</b> {price} VNĐ\n"
            f"🔄 <b>Tiến trình:</b> 🟢 {progress} ✅\n"
            f"⏰ <b>Thời gian Sống:</b> {lifetime}\n"
            f"⏰ <b>Thời gian:</b> {current_time}"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✅ Done", callback_data="done"),
                   types.InlineKeyboardButton("❌ Hủy", callback_data="cancel"))
        markup.add(types.InlineKeyboardButton("🔄 Tiếp tục", callback_data="continue"))

        with open(USER_FILE, "r") as f:
            users = f.read().splitlines()
        
        sent_history = []
        success = 0
        for user in users:
            try:
                sent_msg = bot.send_message(user, html_text, parse_mode="HTML", reply_markup=markup)
                sent_history.append({"chat_id": user, "message_id": sent_msg.message_id})
                success += 1
            except: continue
        
        save_sent_log(sent_history)
        bot.send_message(ADMIN_ID, f"🚀 Bảng Bill đã được gửi tới {success} người.")

    except Exception as e:
        bot.reply_to(message, "❌ Lỗi định dạng! Hãy dùng dấu `|` để ngăn cách.")

# 4. Thu hồi tin nhắn / Bill
@bot.message_handler(commands=['delall'])
def delete_broadcast(message):
    if message.from_user.id == ADMIN_ID:
        history = get_sent_log()
        if not history:
            bot.reply_to(message, "❌ Không có lịch sử gửi để xóa.")
            return

        bot.send_message(ADMIN_ID, f"⏳ Đang thu hồi {len(history)} mục...")
        deleted_count = 0
        for item in history:
            try:
                bot.delete_message(item['chat_id'], item['message_id'])
                deleted_count += 1
            except: pass
        
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        bot.send_message(ADMIN_ID, f"✅ Đã thu hồi thành công {deleted_count} mục.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    bot.answer_callback_query(call.id, f"Trạng thái: {call.data}")

print(f"Bot của {ADMIN_NAME} Media đang hoạt động...")
bot.infinity_polling()