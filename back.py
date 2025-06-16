from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from bs4 import BeautifulSoup
import urllib.parse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
import asyncio
import httpx
import secrets
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time


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
entries_collection = db["entries"]
users_collection = db["users_collection"]
valid_cluster_collection = db["cluster_reports"]
valid_cluster_countries_collection1 = db["valid_cluster_country1"]
valid_cluster_countries_collection2 = db["valid_cluster_country2"]
valid_cluster_countries_collection3 = db["valid_cluster_country3"]
valid_cluster_companies_collection = db["valid_cluster_company"]
################################################################################################fastapi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # back.py가 있는 디렉토리
STATIC_DIR = os.path.join(BASE_DIR, "static")            # 같은 폴더 안에 static 폴더를 두고 싶다면
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")      # 같은 폴더 안에 static 폴더를 두고 싶다면

def user_insert_mongo(user: dict, collection):
    if not collection.find_one({"email": user.get("email")}):
        collection.insert_one(user)
    return None
    

async def fetch_single_ticker(client: httpx.AsyncClient, symbol: str, name: str) -> dict:
    try:
        encoded_symbol = urllib.parse.quote(symbol, safe='')
        url = f"https://finance.yahoo.com/quote/{encoded_symbol}"
        resp = await client.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        quote_section = soup.find("section", {"data-testid": "quote-price"})
        if not quote_section:
            raise ValueError("가격 섹션을 찾을 수 없음")

        inner_soup = BeautifulSoup(str(quote_section), "html.parser")
        price_tag = inner_soup.find("span", {"data-testid": "qsp-price"})
        change_tag = inner_soup.find("span", {"data-testid": "qsp-price-change-percent"})

        price = float(price_tag.text.replace(",", "").strip()) if price_tag else "N/A"
        change = change_tag.text.strip("()%+ ").replace(",", "") if change_tag else "N/A"

        return {
            "name": name,
            "price": price,
            "change": round(float(change), 2) if change != "N/A" else "N/A"
        }

    except Exception:
        return {
            "name": name,
            "price": "N/A",
            "change": "N/A"
        }

async def fetch_ticker_data_async(ticker_dict: dict[str, str]) -> list[dict]:
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, http2=False, follow_redirects=True) as client:
        tasks = [
            fetch_single_ticker(client, symbol, name)
            for symbol, name in ticker_dict.items()
        ]
        return await asyncio.gather(*tasks)
    
def chunk(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def entries_to_og_dict(entries: list[dict]) -> dict:
    og_dict = {}
    for article in entries:
        key = article.get("url", "")
        value = {
            "title": article.get("title",""),
            "desc": article.get("summary", ""),
            "image": article.get("image_url", ""),
            "url": key
            }
        og_dict[key] = value

    return og_dict

def insert_og_dict(clusters: list[dict], og_dict: dict) -> list[dict]:
    new_clusters = []
    for cluster in clusters:
        cluster["og_data"] = []
        for url in cluster["links"]:
            og_data = og_dict.get(url, {"title": "", "desc": "", "image": "", "url": url})
            cluster["og_data"].append(og_data)
        new_clusters.append(cluster)

    return new_clusters

def date_filter(clusters: list[dict], cutoff: int) -> list[dict]:
    threshold = datetime.now() - timedelta(days=cutoff)

    def is_recent(doc):
        try:
            dt_str = doc["cluster_id"].split("_")[0] 
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            return dt >= threshold
        except Exception:
            return False

    return [doc for doc in clusters if is_recent(doc)]


app = FastAPI()

API_KEY = os.getenv('API_KEY')

# static 경로 mount
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY")
)


# templates 설정
templates = Jinja2Templates(directory=TEMPLATES_DIR)

config = Config(environ={
    'GOOGLE_CLIENT_ID': os.getenv("GOOGLE_CLIENT_ID"),
    'GOOGLE_CLIENT_SECRET': os.getenv("GOOGLE_CLIENT_SECRET")
})

oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    nonce = secrets.token_hex(16)
    request.session["nonce"] = nonce
    return await oauth.google.authorize_redirect(request, redirect_uri, nonce = nonce)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # 모든 세션 키 제거
    return RedirectResponse(url="/")

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    nonce = request.session.get("nonce")
    user = await oauth.google.parse_id_token(token, nonce=nonce)
    request.session['user'] = dict(user)
    user_insert_mongo(user, users_collection)


    # user 정보 예: {'email': 'abc@gmail.com', 'name': 'John Doe', ...}
    # 사용자 데이터베이스와 연동하거나 세션 생성
    return RedirectResponse(url="/")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user = request.session.get("user")

    # 1. MongoDB 문서 가져오기
    entries = list(entries_collection.find({}).sort("_id"))
    entries = entries_to_og_dict(entries)

    valid_cluster_documents = insert_og_dict(list(valid_cluster_collection.find({}).sort("_id", -1)), entries)
    valid_cluster_documents = date_filter(valid_cluster_documents, 1)
    valid_cluster_countries_documents1 = insert_og_dict(list(valid_cluster_countries_collection1.find({}).sort("_id", -1)), entries)
    valid_cluster_countries_documents1 = date_filter(valid_cluster_countries_documents1, 1)
    valid_cluster_countries_documents2 = insert_og_dict(list(valid_cluster_countries_collection2.find({}).sort("_id", -1)), entries)
    valid_cluster_countries_documents2 = date_filter(valid_cluster_countries_documents2, 1)
    valid_cluster_countries_documents3 = insert_og_dict(list(valid_cluster_countries_collection3.find({}).sort("_id", -1)), entries)
    valid_cluster_countries_documents3 = date_filter(valid_cluster_countries_documents3, 1)
    valid_cluster_companies_documents = insert_og_dict(list(valid_cluster_companies_collection.find({}).sort("_id", -1)), entries)
    valid_cluster_companies_documents = date_filter(valid_cluster_companies_documents, 1)

    # valid_cluster를 3개씩 묶음
    countries_clusters1_group = chunk(valid_cluster_countries_documents1, 3)
    # valid_cluster를 3개씩 묶음
    countries_clusters2_group = chunk(valid_cluster_countries_documents2, 3)
    # valid_cluster를 3개씩 묶음
    countries_clusters3_group = chunk(valid_cluster_countries_documents3, 3)

    start=time.time()


    
    end = time.time()
    print(f"{end - start:.5f} sec")

    # 3. 티커 데이터 수집

    tickers = {"^KS11":"KOSPI",
            "KRW=X":"KRW/USD",
            "^KQ11":"KOSDAQ", 
            "^GSPC":"S&P500",
            "^IXIC":"NASDAQ", 
            "^DJI":"Dow Jones", 
            "^N225":"Nikkei", 
            "000001.SS":"SSE"}
    result = await fetch_ticker_data_async(tickers)

    # 4. 템플릿 렌더링
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": user,
        "tickers": result,
        "valid_cluster": valid_cluster_documents,
        "valid_cluster_countries1_group": countries_clusters1_group,
        "valid_cluster_countries2_group": countries_clusters2_group,
        "valid_cluster_countries3_group": countries_clusters3_group,
        "valid_cluster_countries1": valid_cluster_countries_documents1,
        "valid_cluster_countries2": valid_cluster_countries_documents2,
        "valid_cluster_countries3": valid_cluster_countries_documents3,
        "valid_cluster_companies": valid_cluster_companies_documents

    })
