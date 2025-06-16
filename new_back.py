from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
import secrets
import os
from dotenv import load_dotenv

#uvicorn new_back:app --reload

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

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

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "1234")
)

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    nonce = secrets.token_hex(16)
    request.session["nonce"] = nonce
    return await oauth.google.authorize_redirect(request, redirect_uri, nonce = nonce)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    nonce = request.session.get("nonce")
    user = await oauth.google.parse_id_token(token, nonce=nonce)

    # user 정보 예: {'email': 'abc@gmail.com', 'name': 'John Doe', ...}
    # 사용자 데이터베이스와 연동하거나 세션 생성
    return RedirectResponse(url="/")

@app.get("/", response_class=FileResponse)
async def serve_cached_page():
    return FileResponse("cached_index.html", media_type="text/html")

@app.get("/logined")
async def logined(request: Request):
