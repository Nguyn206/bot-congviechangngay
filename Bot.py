from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import pandas as pd
from datetime import datetime

from flask import Flask
from threading import Thread

import os

# =====================================
# TELEGRAM
# =====================================

BOT_TOKEN = "8812970343:AAFz_GeUmTinZpYS9Hv9cArpN-Ky_CbNVMA"

# =====================================
# GOOGLE SHEET
# =====================================

SHEET_ID = "1rjag845sSk_CCWgOzowFqmWKRjwibM_4IWYgCDelOt4"

CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=0"
)

# =====================================
# CẤU HÌNH
# =====================================

WAIT_DAYS = 6
GMAIL_PER_LO = 17

# =====================================
# XỬ LÝ NGÀY
# =====================================

def parse_date(date_text):
    try:
        date_text = str(date_text).strip()

        day, month = date_text.split("-")

        now = datetime.now()

        return datetime(
            now.year,
            int(month),
            int(day)
        )

    except:
        return None

# =====================================
# KIỂM TRA LÔ
# =====================================

def check_lo():

    df = pd.read_csv(
        CSV_URL,
        header=None
    )

    available_los = []
    report_lines = []

    today = datetime.now()

    today = datetime(
        today.year,
        today.month,
        today.day
    )

    for row in range(len(df)):

        try:

            value = df.iloc[row, 4]

            if pd.isna(value):
                continue

            lo_name = str(value).strip()

            if not lo_name.startswith("Lo_"):
                continue

            last_mark_date = None

            # Duyệt từ cột G đến cột cuối
            for day_col in range(6, len(df.columns)):

                found = False

                for gmail_row in range(
                    row + 1,
                    min(
                        row + GMAIL_PER_LO + 1,
                        len(df)
                    )
                ):

                    cell = df.iloc[
                        gmail_row,
                        day_col
                    ]

                    if pd.isna(cell):
                        continue

                    cell_text = str(
                        cell
                    ).strip().lower()

                    if cell_text == "":
                        continue

                    if cell_text == "lỗi":
                        continue

                    date_text = str(
                        df.iloc[0, day_col]
                    ).strip()

                    last_mark_date = parse_date(
                        date_text
                    )

                    found = True
                    break

                if found:
                    break

            # Chưa từng làm
            if last_mark_date is None:

                available_los.append(
                    lo_name
                )

                report_lines.append(
                    f"🟡 {lo_name}: CHƯA TỪNG LÀM"
                )

                continue

            days_waited = (
                today -
                last_mark_date
            ).days

            print(
                lo_name,
                last_mark_date.strftime("%d-%m"),
                days_waited
            )

            if days_waited >= WAIT_DAYS:

                available_los.append(
                    lo_name
                )

                report_lines.append(
                    f"🟡 {lo_name}: {days_waited} ngày"
                )

            else:

                remain = WAIT_DAYS - days_waited

                report_lines.append(
                    f"🔴 {lo_name}: còn {remain} ngày"
                )

        except Exception as e:

            print(
                f"Lỗi xử lý dòng {row}: {e}"
            )

    return available_los, report_lines

# =====================================
# /START
# =====================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        ["🔍 KIỂM TRA"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🤖 BOT KIỂM TRA LÔ\n\nBấm nút bên dưới để kiểm tra.",
        reply_markup=reply_markup
    )

# =====================================
# XỬ LÝ NÚT
# =====================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    if text != "🔍 KIỂM TRA":
        return

    try:

        los, report = check_lo()

        if los:

            message = (
                "📋 DANH SÁCH LÔ CÓ THỂ LÀM\n\n"
            )

            for lo in los:

                message += (
                    f"🟡 {lo}\n"
                )

            message += (
                f"\nTổng cộng: {len(los)} lô\n\n"
            )

        else:

            message = (
                "❌ Không có lô nào đủ điều kiện.\n\n"
            )

        message += (
            "====================\n"
        )

        message += "\n".join(report)

        await update.message.reply_text(
            message
        )

    except Exception as e:

        await update.message.reply_text(
            f"Lỗi:\n{str(e)}"
        )

# =====================================
# WEB SERVER CHO RENDER
# =====================================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Telegram dang chay!"

def run_web():
    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port
    )

# =====================================
# CHẠY BOT
# =====================================

app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT,
        handle_message
    )
)

print("=================================")
print("BOT ĐANG CHẠY...")
print("=================================")

Thread(
    target=run_web,
    daemon=True
).start()

app.run_polling()