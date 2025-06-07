# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 생성
WORKDIR /app

# 시스템 패키지 설치 (예: MongoDB와 관련된 네트워크 기능을 위해)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치에 필요한 파일 복사
COPY requirements.txt .

# 종속성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 코드 복사
COPY . .

# 환경변수 로드용 dotenv 파일 복사(선택)
COPY .env .env

# FastAPI를 uvicorn으로 실행
CMD ["uvicorn", "new_back:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
