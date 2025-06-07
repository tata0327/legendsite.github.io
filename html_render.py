# generate_static_html.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
import requests
import urllib.parse

# Load env
load_dotenv()
uri = os.getenv("MONGO_DB_URI")

# Mongo connection
client = MongoClient(uri)
db = client["test_db"]
valid_cluster_collection = db["cluster_reports"]
valid_cluster_countries_collection1 = db["valid_cluster_country1"]
valid_cluster_countries_collection2 = db["valid_cluster_country2"]
valid_cluster_countries_collection3 = db["valid_cluster_country3"]

# Template env setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
template = env.get_template("index.html")

def fetch_og_meta(url: str) -> dict:
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')

        def get_meta(prop):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            return tag["content"] if tag and tag.has_attr("content") else ""

        return {
            "url": url,
            "title": get_meta("og:title"),
            "desc": get_meta("og:description"),
            "image": get_meta("og:image")
        }
    except Exception:
        return {"url": url, "title": "", "desc": "", "image": ""}

def fetch_ticker_data(ticker_dict: dict[str, str]) -> list[dict]:
    result = []
    headers = {"User-Agent": "Mozilla/5.0"}

    for symbol, name in ticker_dict.items():
        try:
            encoded = urllib.parse.quote(symbol, safe='')
            url = f"https://finance.yahoo.com/quote/{encoded}"
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')

            quote_section = soup.find("section", {"data-testid": "quote-price"})
            inner_soup = BeautifulSoup(str(quote_section), "html.parser")

            price_tag = inner_soup.find("span", {"data-testid": "qsp-price"})
            change_tag = inner_soup.find("span", {"data-testid": "qsp-price-change-percent"})

            price = float(price_tag.text.replace(",", "").strip()) if price_tag else "N/A"
            change = change_tag.text.strip("()%+ ").replace(",", "") if change_tag else "N/A"

            result.append({
                "name": name,
                "price": price,
                "change": round(float(change), 2) if change != "N/A" else "N/A"
            })
        except Exception:
            result.append({"name": name, "price": "N/A", "change": "N/A"})

    return result

def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def generate_html():
    # 1. 데이터 불러오기
    valid_cluster_documents = list(valid_cluster_collection.find({}).sort("_id", -1))
    valid_cluster_countries_documents1 = list(valid_cluster_countries_collection1.find({}).sort("_id", -1))
    valid_cluster_countries_documents2 = list(valid_cluster_countries_collection2.find({}).sort("_id", -1))
    valid_cluster_countries_documents3 = list(valid_cluster_countries_collection3.find({}).sort("_id", -1))

    # valid_cluster를 3개씩 묶음
    countries_clusters1_group = chunk(valid_cluster_countries_documents1, 3)
    # valid_cluster를 3개씩 묶음
    countries_clusters2_group = chunk(valid_cluster_countries_documents2, 3)
    # valid_cluster를 3개씩 묶음
    countries_clusters3_group = chunk(valid_cluster_countries_documents3, 3)


    # 2. URL 기반 OG 메타데이터 카드 생성
    embeds_issue = [
        [fetch_og_meta(link) for link in doc["links"]]
        for doc in valid_cluster_documents[:7]
        if "links" in doc
    ]

    embeds_countries1 = [
        [fetch_og_meta(link) for link in doc["links"]]
        for doc in valid_cluster_countries_documents1
        if "links" in doc
    ]

    embeds_countries2 = [
        [fetch_og_meta(link) for link in doc["links"]]
        for doc in valid_cluster_countries_documents2
        if "links" in doc
    ]

    embeds_countries3 = [
        [fetch_og_meta(link) for link in doc["links"]]
        for doc in valid_cluster_countries_documents3
        if "links" in doc
    ]

    embeds_countries = [embeds_countries1, embeds_countries2, embeds_countries3]

    embeds_issue = [
        [fetch_og_meta(link) for link in doc.get("links", [])]
        for doc in valid_cluster_documents[:7]
    ]

    tickers = {
        "^KS11":"KOSPI", "KRW=X":"KRW/USD", "^KQ11":"KOSDAQ",
        "^GSPC":"S&P500", "^IXIC":"NASDAQ", "^DJI":"Dow Jones",
        "^N225":"Nikkei", "000001.SS":"SSE"
    }
    ticker_data = fetch_ticker_data(tickers)

    # 2. 템플릿 렌더링
    html = template.render(
        request=None,
        valid_cluster=valid_cluster_documents,
        valid_cluster_countries1_group=countries_clusters1_group,
        valid_cluster_countries2_group=countries_clusters2_group,
        valid_cluster_countries3_group=countries_clusters3_group,
        valid_cluster_countries1 = valid_cluster_countries_documents1,
        valid_cluster_countries2 = valid_cluster_countries_documents2,
        valid_cluster_countries3 = valid_cluster_countries_documents3,
        embeds_countries=embeds_countries,
        embeds=embeds_issue,
        tickers=ticker_data
    )

    # 3. 저장
    with open("cached_index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("cached_index.html 생성 완료")

if __name__ == "__main__":
    generate_html()
