import os
import time
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from telegram import Bot
from datetime import datetime

# ---------------- CONFIG ---------------- #
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PINCODES = ["733134", "733215", "201014", "110092"]
CHECK_INTERVAL = 1800  # 30 minutes (safe)

JIOMART_QUICK_URL = "https://www.jiomart.com/c/groceries/2"
# --------------------------------------- #

bot = Bot(token=BOT_TOKEN)

sent_products = {p: set() for p in PINCODES}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Linux; Android 10)"
    )

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def set_pincode(driver, pincode):
    driver.get("https://www.jiomart.com")
    time.sleep(5)

    try:
        pincode_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Pincode')]")
        pincode_btn.click()
        time.sleep(2)

        input_box = driver.find_element(By.XPATH, "//input[@type='text']")
        input_box.clear()
        input_box.send_keys(pincode)
        input_box.send_keys(Keys.ENTER)
        time.sleep(4)

        log(f"Pincode set: {pincode}")
    except:
        log("Pincode already set or selector changed")


def get_quick_deals(driver):
    driver.get(JIOMART_QUICK_URL)
    time.sleep(8)

    deals = []

    products = driver.find_elements(By.XPATH, "//div[contains(@class,'plp-card')]")

    for p in products:
        try:
            discount_text = p.text.lower()
            if "%" not in discount_text:
                continue

            discount = int(discount_text.split("%")[0].split()[-1])
            if discount < 70 or discount > 99:
                continue

            name = p.find_element(By.XPATH, ".//span").text
            link = p.find_element(By.XPATH, ".//a").get_attribute("href")

            price = "N/A"
            mrp = "N/A"

            deals.append({
                "id": link,
                "name": name,
                "discount": discount,
                "price": price,
                "mrp": mrp,
                "url": link
            })
        except:
            continue

    return deals


async def send_grouped(pincode, deals):
    if not deals:
        return

    msg = [
        "🔥 *JioMart QUICK Deals*",
        f"📍 *Pincode:* `{pincode}`",
        ""
    ]

    for d in deals:
        msg.append(
            f"• *{d['discount']}% OFF* — {d['name']}\n"
            f"  🔗 {d['url']}\n"
        )

    await bot.send_message(
        chat_id=CHAT_ID,
        text="\n".join(msg),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


async def main():
    log("🚀 SELENIUM JIOMART QUICK DEAL MONITOR STARTED")

    driver = create_driver()

    while True:
        for pincode in PINCODES:
            set_pincode(driver, pincode)
            deals = get_quick_deals(driver)

            new = []
            for d in deals:
                if d["id"] not in sent_products[pincode]:
                    sent_products[pincode].add(d["id"])
                    new.append(d)

            if new:
                await send_grouped(pincode, new)
                log(f"{pincode}: {len(new)} deals sent")

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
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
