import os
import asyncio
import requests
from telegram import Bot
from datetime import datetime

# ---------------- CONFIG ---------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PINCODES = ["733134", "733215", "201014", "110092"]
CHECK_INTERVAL = 600  # 10 minutes

API_URL = "https://www.jiomart.com/api/search"
# --------------------------------------- #

bot = Bot(token=BOT_TOKEN)

# Track already-alerted products per pincode
sent_products = {pincode: set() for pincode in PINCODES}


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def fetch_quick_deals(pincode):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "query": "",
        "page": 1,
        "rows": 50,
        "pincode": pincode,
        "serviceabilityTags": ["JIOMART_QUICK"],
        "sort": "discount_desc"
    }

    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        data = r.json()

        deals = []
        for p in data.get("products", []):
            discount = p.get("discount", 0)

            if 70 <= discount <= 99:
                deals.append({
                    "id": p["id"],
                    "name": p["displayName"],
                    "discount": discount,
                    "mrp": p.get("mrp"),
                    "price": p.get("sellingPrice"),
                    "url": "https://www.jiomart.com/p/" + p["seoUrl"]
                })

        return deals

    except Exception as e:
        log(f"API error ({pincode}): {e}")
        return []


async def send_grouped_message(pincode, deals):
    if not deals:
        return

    lines = [
        f"🔥 *JioMart QUICK Deals*",
        f"📍 *Pincode:* `{pincode}`",
        ""
    ]

    for d in deals:
        lines.append(
            f"• *{d['discount']}% OFF* — {d['name']}\n"
            f"  ₹{d['price']} (MRP ₹{d['mrp']})\n"
            f"  🔗 {d['url']}\n"
        )

    message = "\n".join(lines)

    await bot.send_message(
        chat_id=CHAT_ID,
        text=message,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


async def main():
    log("🚀 Monitoring JioMart QUICK 70–99% OFF deals (Grouped per Pincode)")

    while True:
        for pincode in PINCODES:
            all_deals = fetch_quick_deals(pincode)

            # Filter only NEW deals
            new_deals = []
            for d in all_deals:
                if d["id"] not in sent_products[pincode]:
                    new_deals.append(d)
                    sent_products[pincode].add(d["id"])

            if new_deals:
                await send_grouped_message(pincode, new_deals)
                log(f"Grouped alert sent ({pincode}): {len(new_deals)} deals")

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
