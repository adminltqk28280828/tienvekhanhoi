import time
import os
import json
import telebot
import datetime
from telebot import types
from datetime import datetime as dt
from colorama import Fore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- THÔNG TIN CẤU HÌNH ---
TOKEN = "8562421632:AAEqooqs8sqi5DSincjE1l3Ld53YkBBI0yw"
ADMIN_ID = 6684980246
BRAND = "QUOC KHANH MEDIA"
USER_FILE = "users.txt"
LOG_FILE = "sent_messages.json"

bot = telebot.TeleBot(TOKEN)
is_running = False  
stop_flag = False 

# --- HÀM HỖ TRỢ HỆ THỐNG ---
def save_user(user_id):
    user_id = str(user_id)
    if not os.path.exists(USER_FILE): open(USER_FILE, "w").close()
    with open(USER_FILE, "a+") as f:
        f.seek(0)
        users = f.read().splitlines()
        if user_id not in users: f.write(user_id + "\n")

def get_all_users():
    if not os.path.exists(USER_FILE): return []
    with open(USER_FILE, "r") as f: return f.read().splitlines()

def save_sent_log(log_data):
    with open(LOG_FILE, "w") as f: json.dump(log_data, f)

def get_sent_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f: return json.load(f)
    return []

# --- HÀM BROADCAST CHUNG ---
def broadcast_all(content, is_html=True, markup=None):
    users = get_all_users()
    sent_history = []
    success = 0
    parse_mode = "HTML" if is_html else None
    
    for user_id in users:
        try:
            sent_msg = bot.send_message(user_id, content, parse_mode=parse_mode, reply_markup=markup)
            sent_history.append({"chat_id": user_id, "message_id": sent_msg.message_id})
            success += 1
        except: continue
    
    save_sent_log(sent_history)
    return success

# --- AUTOMATION LOGIC ---
class QKMediaAutomation:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
        self.wait = WebDriverWait(self.driver, 10)

    def turbo_click(self, selectors):
        for xpath in selectors:
            try:
                element = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except: continue
        return False

# --- XỬ LÝ LỆNH BOT ---

@bot.message_handler(commands=['start'])
def welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, f"🌟 Chào mừng đến với <b>{BRAND}</b>!\nID của bạn đã được ghi nhận.", parse_mode="HTML")

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id == ADMIN_ID:
        users = get_all_users()
        bot.reply_to(message, f"📊 Tổng cộng: {len(users)} người dùng đang sử dụng bot.")

@bot.message_handler(commands=['stop'])
def stop_process(message):
    global stop_flag
    if message.from_user.id == ADMIN_ID:
        stop_flag = True
        bot.reply_to(message, "🛑 Đang gửi lệnh dừng hệ thống...")

@bot.message_handler(commands=['delall'])
def delete_broadcast(message):
    if message.from_user.id == ADMIN_ID:
        history = get_sent_log()
        if not history: return bot.reply_to(message, "❌ Không có gì để xóa.")
        
        deleted = 0
        for item in history:
            try:
                bot.delete_message(item['chat_id'], item['message_id'])
                deleted += 1
            except: pass
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
        bot.send_message(ADMIN_ID, f"✅ Đã thu hồi {deleted} tin nhắn.")

@bot.message_handler(commands=['send'])
def manual_send(message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace('/send', '').strip()
        if not text: return bot.reply_to(message, "Nhập nội dung sau /send")
        num = broadcast_all(f"📢 <b>THÔNG BÁO TỪ ADMIN</b>\n\n{text}")
        bot.send_message(ADMIN_ID, f"✅ Đã gửi tới {num} người.")

@bot.message_handler(commands=['bill'])
def create_bill(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = [p.strip() for p in message.text.replace('/bill', '').split('|')]
        uid, status, name, note, price, progress, lifetime = parts
        icon = "❌" if "DIE" in status.upper() else "✅"
        header = f"{icon} {status} rồi sếp ơi Quốc Khánh!"
        
        html = (f"<b>{header}</b>\n\nUID {uid} - {status.upper()} {icon}\n"
                f"👤 <b>Tên:</b> {name}\n📝 <b>Ghi chú:</b> {note}\n💵 <b>Giá:</b> {price}\n"
                f"🔄 <b>Tiến trình:</b> {progress}\n⏰ <b>Thời gian:</b> {dt.now().strftime('%H:%M:%S')}")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Done", callback_data="d"), types.InlineKeyboardButton("❌ Hủy", callback_data="c"))
        
        broadcast_all(html, markup=markup)
        bot.send_message(ADMIN_ID, "🚀 Đã phát sóng bảng Bill!")
    except: bot.reply_to(message, "⚠️ Lỗi định dạng |")

# --- XỬ LÝ AUTOMATION (CATCH-ALL) ---
@bot.message_handler(func=lambda message: True)
def handle_automation(message):
    global is_running, stop_flag
    if message.from_user.id != ADMIN_ID: return
    if ':::' not in message.text: return # Bỏ qua nếu không đúng cấu hình
    
    if is_running: return bot.reply_to(message, "⚠️ Hệ thống đang bận!")

    try:
        parts = message.text.split(':::')
        target, cookie, repeat = parts[0].strip(), parts[1].strip(), int(parts[2].strip())
        
        is_running, stop_flag = True, False
        auto = QKMediaAutomation()
        
        # Bắt đầu vòng lặp
        for i in range(1, repeat + 1):
            if stop_flag: break
            
            # Logic update tiến trình cho mọi người
            progress_msg = (f"🚀 <b>{BRAND} - MONITOR</b>\n"
                            f"🎯 Mục tiêu: <code>{target}</code>\n"
                            f"📊 Lượt: {i}/{repeat}\n Trạng thái: <b>ĐANG CHẠY</b>")
            broadcast_all(progress_msg)
            
            time.sleep(5) # Giả lập thời gian chạy selenium

        auto.driver.quit()
        is_running = False
        broadcast_all(f"✅ <b>HOÀN THÀNH CHIẾN DỊCH</b>\n🎯 Đối tượng: {target}")

    except Exception as e:
        is_running = False
        bot.reply_to(message, f"❌ Lỗi: {e}")

bot.callback_query_handler(func=lambda call: True)(lambda call: bot.answer_callback_query(call.id, "Đã ghi nhận"))

print("--- HỆ THỐNG HỢP NHẤT QUỐC KHÁNH MEDIA ĐÃ ONLINE ---")
bot.infinity_polling()