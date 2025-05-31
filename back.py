from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from bs4 import BeautifulSoup
import requests
import urllib.parse
from dotenv import load_dotenv


#uvicorn back:app --reload

# 환경 변수 로드
load_dotenv()

uri = os.getenv('MONGO_DB_URI')

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# 데이터베이스와 컬렉션 선택
db = client["test_db"]
test_collection = db["test_collection"]
raw_data_collection = db["raw_data"]
valid_cluster_collection = db["valid_cluster"]
valid_cluster_company_collection1 = db["valid_cluster_company1"]
valid_cluster_company_collection2 = db["valid_cluster_company1"]
valid_cluster_company_collection3 = db["valid_cluster_company1"]
################################################################################################fastapi

app = FastAPI()

STATIC_DIR = "C:/Users/김우영/Desktop/목숨을 걸었어/test/newsbot/webpage/back/static"
TEMPLATES_DIR = "C:/Users/김우영/Desktop/목숨을 걸었어/test/newsbot/webpage/back/templates"
API_KEY = os.getenv('API_KEY')

# static 경로 mount
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# templates 설정
templates = Jinja2Templates(directory=TEMPLATES_DIR)

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
        return {
            "url": url,
            "title": "",
            "desc": "",
            "image": ""
        }
    
def fetch_ticker_data(ticker_dict: dict[str, str]) -> list[dict]:
    result = []
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for symbol, name in ticker_dict.items():
        try:
            encoded_symbol = urllib.parse.quote(symbol, safe='')
            url = f"https://finance.yahoo.com/quote/{encoded_symbol}"
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            quote_section = soup.find("section", {"data-testid": "quote-price"})
            if not quote_section:
                raise ValueError("가격 섹션을 찾을 수 없음")

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
            result.append({
                "name": name,
                "price": "N/A",
                "change": "N/A"
            })

    return result

def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 1. MongoDB 문서 가져오기
    documents = list(test_collection.find({}, {"_id": 0}))
    raw_documents = list(raw_data_collection.find({}, {"_id": 0}))
    valid_cluster_documents = list(valid_cluster_collection.find({}, {"_id": 0})) 
    valid_cluster_company_documents1 = list(valid_cluster_company_collection1.find({}, {"id":0}))
    valid_cluster_company_documents2 = list(valid_cluster_company_collection2.find({}, {"id":0}))
    valid_cluster_company_documents3 = list(valid_cluster_company_collection3.find({}, {"id":0}))
    # valid_cluster_people를 3개씩 묶음
    company_clusters1_group = chunk(valid_cluster_company_documents1, 3)
    # valid_cluster_people를 3개씩 묶음
    company_clusters2_group = chunk(valid_cluster_company_documents2, 3)
    # valid_cluster_people를 3개씩 묶음
    company_clusters3_group = chunk(valid_cluster_company_documents3, 3)

    # 2. URL 기반 OG 메타데이터 카드 생성
    embeds = [fetch_og_meta(doc["url"]) for doc in raw_documents if "url" in doc]

    tickers = {"^KS11":"KOSPI",
            "KRW=X":"KRW/USD",
            "^KQ11":"KOSDAQ", 
            "^GSPC":"S&P500",
            "^IXIC":"NASDAQ", 
            "^DJI":"Dow Jones", 
            "^N225":"Nikkei", 
            "000001.SS":"SSE"}
    result = fetch_ticker_data(tickers)

    # 4. 템플릿 렌더링
    return templates.TemplateResponse("index.html", {
        "request": request,
        "documents": documents,
        "tickers": result,
        "embeds": embeds,
        "valid_cluster": valid_cluster_documents,
        "valid_cluster_company1_group": company_clusters1_group,
        "valid_cluster_company2_group": company_clusters2_group,
        "valid_cluster_company3_group": company_clusters3_group,
        "valid_cluster_company1": valid_cluster_company_documents1,
        "valid_cluster_company2": valid_cluster_company_documents2,
        "valid_cluster_company3": valid_cluster_company_documents3

    })
