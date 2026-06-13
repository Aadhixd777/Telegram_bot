import asyncio
import requests
import re
import phonenumbers
from phonenumbers import geocoder
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

BOT_TOKEN = "8825805424:AAENFLuq4M3w-BTl9XRI221gNcLSwqeSOH4"
bot = Bot(token=BOT_TOKEN)

GROUP_IDS = [
    --1003901583807,

]

API_URLS = [
    "http://mis-panel-production.up.railway.app/api/junaid?type=sms",
    "http://mis-panel-production.up.railway.app/api/junaid?type=sms",
    "https://number-panel-production.up.railway.app/api/junaid?type=sms",
    "http://mis-panel-production.up.railway.app/api/gijunaid?type=sms",
    "https://hadibhai-production-90b2.up.railway.app/api/psjunaid?type=sms",
    "https://ims-panel-production.up.railway.app/api/junaidn?type=sms",
    
]

def fetch_latest_otp(api_url):
    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()
        records = data.get("aaData", [])
        valid = [r for r in records if isinstance(r[0], str) and ":" in r[0]]
        if not valid:
            return None
        latest = valid[0]
        return {
            "time": latest[0],
            "country": latest[1],
            "number": latest[2],
            "service": latest[3],
            "message": latest[4],
        }
    except Exception as e:
        print(f"Error from {api_url}: {e}")
        return None


def extract_otp(message):
    for pat in [r'\d{3}-\d{3}', r'\d{6}', r'\d{4}']:
        match = re.search(pat, message)
        if match:
            return match.group(0)
    return "N/A"


def mask_number(number_str):
    try:
        number_str = f"+{number_str}"
        length = len(number_str)
        if length < 10:
            show_first = 4
            show_last = 2
        else:
            show_first = 5
            show_last = 4
        stars = '*' * (length - show_first - show_last)
        if len(stars) < 0:
            return number_str
        return f"{number_str[:show_first]}{stars}{number_str[-show_last:]}"
    except:
        return f"+{number_str}"


def get_country_info_from_number(number_str):
    try:
        if not number_str.startswith("+"):
            number_str = f"+{number_str}"
        parsed = phonenumbers.parse(number_str)
        country_name = geocoder.description_for_number(parsed, "en")
        region_code = phonenumbers.region_code_for_number(parsed)
        if region_code:
            base = 127462 - ord("A")
            flag = chr(base + ord(region_code[0])) + chr(base + ord(region_code[1]))
        else:
            flag = "🌍"
        return country_name or "Unknown", flag
    except:
        return "Unknown", "🌍"


def format_message(record):
    raw = record["message"]
    otp = extract_otp(raw)
    msg = raw.replace("<", "&lt;").replace(">", "&gt;")
    country_name, flag = get_country_info_from_number(record["number"])
    formatted_number = mask_number(record["number"])
    service_icon = "📱"
    s = record["service"].lower()
    if "whatsapp" in s:
        service_icon = "🟢"
    elif "telegram" in s:
        service_icon = "🔵"
    elif "facebook" in s:
        service_icon = "📘"
    return f"""
<b>{flag} New {country_name} {record['service']} OTP!</b>

<blockquote>🕰 Time: {record['time']}</blockquote>
<blockquote>{flag} Country: {country_name}</blockquote>
<blockquote>{service_icon} Service: {record['service']}</blockquote>
<blockquote>📞 Number: {formatted_number}</blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>

<blockquote>📩 Full Message:</blockquote>
<pre>{msg}</pre>

Powered by Aadhixd 
"""


async def send_to_all_groups(message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="☎️ Number", url="https://t.me/junaidaliniz"),
            InlineKeyboardButton(text="☎️ Number", url="https://t.me/junaidaliniz")
        ]
    ])
    for group in GROUP_IDS:
        try:
            await bot.send_message(
                chat_id=group,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except Exception as e:
            print(f"Error sending to group {group}: {e}")


async def api_worker(api_url):
    print(f"[STARTED] Worker for {api_url}")
    last_number = None
    while True:
        otp = fetch_latest_otp(api_url)
        if otp:
            if otp["number"] != last_number:
                last_number = otp["number"]
                msg = format_message(otp)
                await send_to_all_groups(msg)
                print(f"[{datetime.now()}] Sent new OTP from {otp['number']} | API: {api_url}")
        await asyncio.sleep(3)


async def main():
    print("Starting multi-API, multi-group OTP bot...")
    tasks = [asyncio.create_task(api_worker(api)) for api in API_URLS]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
