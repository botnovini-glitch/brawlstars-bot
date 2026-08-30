import feedparser
import time
import requests
from telegram import Bot
from twscrape import API
import asyncio
import os

TOKEN = "8643428228:AAGEx_JCMnO6Ojf-Ooj5dHwl--eny8xBjXI"
CHAT_ID = 8976496780
YOUTUBE_API_KEY = "AIzaSyCL25DaM6AUx9-J1Qr889AcM3nXigRAVNI"

REDDIT_FEEDS = [
    "https://www.reddit.com/r/BrawlStars/new/.rss",
    "https://www.reddit.com/r/BrawlStarsCompetitive/new/.rss",
]

seen_links = set()
twitter_api = API()

async def send_message(bot, text):
    await bot.send_message(chat_id=CHAT_ID, text=text)

def check_reddit(bot, loop):
    for url in REDDIT_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.link not in seen_links:
                seen_links.add(entry.link)
                message = f"Reddit: {entry.title}\n{entry.link}"
                loop.run_until_complete(send_message(bot, message))
                print("Надіслано (Reddit):", entry.title)

def is_spammy(title):
    spam_markers = ["1500", "ПРОМОКОД", "ПОДПИШИСЬ", "ДАРМОВІ", "ОДБИЕРЗ", "GRATIS", "FREE GEMS"]
    upper_title = title.upper()
    hashtag_count = title.count("#")
    if hashtag_count >= 5:
        return True
    for marker in spam_markers:
        if marker in upper_title:
            return True
    return False

def check_youtube(bot, loop):
    queries = ["Brawl Stars", "Браво Старс"]
    for query in queries:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "date",
            "maxResults": 10,
            "relevanceLanguage": "uk" if query == "Браво Старс" else "en",
            "key": YOUTUBE_API_KEY,
        }
        response = requests.get(url, params=params)
        data = response.json()
        if "items" not in data:
            print("Помилка YouTube API:", data)
            continue
        for item in data["items"]:
            video_id = item["id"]["videoId"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            title = item["snippet"]["title"]
            if link not in seen_links:
                seen_links.add(link)
                if is_spammy(title):
                    print("Пропущено (спам):", title)
                    continue
                message = f"YouTube: {title}\n{link}"
                loop.run_until_complete(send_message(bot, message))
                print("Надіслано (YouTube):", title)

def check_twitter(bot, loop):
    MIN_LIKES = 5

    async def fetch():
        results = []
        async for tweet in twitter_api.search("Brawl Stars", limit=15):
            results.append(tweet)
        async for tweet in twitter_api.search("Браво Старс", limit=15):
            results.append(tweet)
        return results

    tweets = loop.run_until_complete(fetch())
    for tweet in tweets:
        link = f"https://x.com/{tweet.user.username}/status/{tweet.id}"
        if link not in seen_links:
            seen_links.add(link)
            if tweet.likeCount < MIN_LIKES:
                print("Пропущено (мало лайків):", tweet.rawContent[:50])
                continue
            text = tweet.rawContent[:200]
            message = f"Twitter: {text}\n{link}"
            loop.run_until_complete(send_message(bot, message))
            print("Надіслано (Twitter):", text[:50])
async def setup_twitter():
     await twitter_api.pool.delete_accounts(TWITTER_USERNAME)
     await twitter_api.pool.add_account(
        TWITTER_USERNAME,
        TWITTER_PASSWORD,
        TWITTER_EMAIL,
        TWITTER_EMAIL_PASSWORD,
        cookies=TWITTER_COOKIES
    )
def main():
    bot = Bot(token=TOKEN)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print("Підключення Twitter акаунту...")
    loop.run_until_complete(setup_twitter())
    
    print("Перше сканування (без відправки старих постів)...")
    for url in REDDIT_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            seen_links.add(entry.link)

    print("Моніторинг запущено. Натисни Ctrl+C щоб зупинити.")
    while True:
        check_reddit(bot, loop)
        check_youtube(bot, loop)
        check_twitter(bot, loop)
        time.sleep(180)

main()
