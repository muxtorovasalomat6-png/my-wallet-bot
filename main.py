import asyncio
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile

TOKEN = "8302393783:AAGJYCzDbz9p2peNdTrCP8E-VDBDQgZVoHA"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- TUGMALAR ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Hisobot"), KeyboardButton(text="🗂 Kategoriyalar")],
            [KeyboardButton(text="📈 Grafik"), KeyboardButton(text="📄 Excel yuklash")],
            [KeyboardButton(text="❌ Oxirgisini o'chirish")]
        ],
        resize_keyboard=True
    )

# --- BAZA ---
def init_db():
    conn = sqlite3.connect("xarajatlar.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS xarajatlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            miqdor INTEGER,
            izoh TEXT,
            sana DATE DEFAULT (date('now'))
        )
    """)
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def start_cmd(message: Message):
    init_db()
    await message.answer(f"Salom {message.from_user.first_name}!\nXarajatni yozing (masalan: 15000 tushlik)", reply_markup=get_main_keyboard())

# --- EXCEL YUKLASH (TUZATILDI) ---
@dp.message(F.text == "📄 Excel yuklash")
async def export_excel(message: Message):
    try:
        conn = sqlite3.connect("xarajatlar.db")
        # Ma'lumotlarni o'qishda params ishlatamiz
        query = "SELECT sana as 'Sana', izoh as 'Izoh', miqdor as 'Miqdor' FROM xarajatlar WHERE user_id = ?"
        df = pd.read_sql_query(query, conn, params=(message.from_user.id,))
        conn.close()
        
        if df.empty:
            return await message.answer("Bazada hali ma'lumot yo'q.")
        
        file_name = f"xarajatlar_{message.from_user.id}.xlsx"
        df.to_excel(file_name, index=False)
        
        await message.answer_document(FSInputFile(file_name), caption="Sizning barcha xarajatlaringiz 📄")
        if os.path.exists(file_name):
            os.remove(file_name)
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi. Iltimos botni restart qiling.")

# --- KATEGORIYALAR ---
@dp.message(F.text == "🗂 Kategoriyalar")
async def show_categories(message: Message):
    conn = sqlite3.connect("xarajatlar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT izoh, SUM(miqdor) FROM xarajatlar WHERE user_id = ? GROUP BY izoh", (message.from_user.id,))
    data = cursor.fetchall()
    conn.close()
    if not data: return await message.answer("Ma'lumot yo'q.")
    
    text = "📂 **Kategoriyalar bo'yicha sarf:**\n"
    for i in data:
        text += f"\n🔹 {i[0].capitalize()}: {i[1]} so'm"
    await message.answer(text)

# --- GRAFIK ---
@dp.message(F.text == "📈 Grafik")
async def send_graph(message: Message):
    conn = sqlite3.connect("xarajatlar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT izoh, SUM(miqdor) FROM xarajatlar WHERE user_id = ? GROUP BY izoh", (message.from_user.id,))
    data = cursor.fetchall()
    conn.close()
    if not data: return await message.answer("Ma'lumot yetarli emas.")
    
    plt.figure(figsize=(8, 5))
    plt.pie([i[1] for i in data], labels=[i[0] for i in data], autopct='%1.1f%%')
    plt.title("Xarajatlar taqsimoti")
    plt.savefig("graph.png")
    plt.close()
    await message.answer_photo(FSInputFile("graph.png"), caption="Xarajatlar grafigi 📊")
    os.remove("graph.png")

# --- HISOBOT ---
@dp.message(F.text == "📊 Hisobot")
async def get_report(message: Message):
    conn = sqlite3.connect("xarajatlar.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(miqdor) FROM xarajatlar WHERE user_id = ?", (message.from_user.id,))
    total = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 Sizning umumiy xarajatlaringiz:\n\n💰 **{total if total else 0} so'm**")

# --- O'CHIRISH ---
@dp.message(F.text == "❌ Oxirgisini o'chirish")
async def delete_last(message: Message):
    conn = sqlite3.connect("xarajatlar.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM xarajatlar WHERE id = (SELECT MAX(id) FROM xarajatlar WHERE user_id = ?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    await message.answer("Eng oxirgi yozuv o'chirildi! 🗑✅")

# --- SAQLASH ---
@dp.message()
async def save_expense(message: Message):
    parts = message.text.split(maxsplit=1)
    if parts[0].isdigit():
        amount = int(parts[0])
        reason = parts[1] if len(parts) > 1 else "Boshqa"
        
        conn = sqlite3.connect("xarajatlar.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO xarajatlar (user_id, miqdor, izoh) VALUES (?, ?, ?)", (message.from_user.id, amount, reason))
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ Saqlandi!\n💰 Miqdor: {amount} so'm\n📝 Izoh: {reason}")
    else:
        await message.answer("⚠️ Tushunmadim. Iltimos, xarajatni raqam bilan boshlang.\nMasalan: `5000 yo'l kira`")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())