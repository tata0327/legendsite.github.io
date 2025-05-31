import requests
from bs4 import BeautifulSoup
import urllib.parse

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



# 3. 티커 데이터 수집
tickers = {"^KS11":"KOSPI",
           "KRW=X":"KRW/USD",
           "^KQ11":"KOSDAQ", 
           "^GSPC":"S&P500",
           "^IXIC":"NASDAQ", 
           "^DJI":"Dow Jones", 
           "^N225":"Nikkei", 
           "000001.SS":"SSE"}
result = fetch_ticker_data(tickers)
print(result)