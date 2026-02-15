import pytse_client as tse
import pandas as pd
import json
from datetime import datetime
import jdatetime
import time

def calculate_sma(prices, period):
    return prices.rolling(window=period).mean()

def get_stocks_with_golden_cross():
    # دریافت لیست همه نمادها
    tse.download(symbols="all", write_to_csv=False)
    all_symbols = tse.symbols()  # لیست کامل نمادها
    
    result = []
    # برای جلوگیری از محدودیت، فقط ۵۰ نماد اول رو بررسی می‌کنیم
    for symbol in all_symbols[:50]:
        try:
            ticker = tse.Ticker(symbol)
            history = ticker.history
            if history.empty or len(history) < 26:
                continue
            
            prices = history['adj_close']  # قیمت پایانی تعدیل‌شده
            sma9 = calculate_sma(prices, 9)
            sma26 = calculate_sma(prices, 26)
            
            # آخرین مقدار و دو روز پیش
            if pd.isna(sma9.iloc[-1]) or pd.isna(sma26.iloc[-1]) or len(sma9) < 3:
                continue
            
            current_9 = sma9.iloc[-1]
            current_26 = sma26.iloc[-1]
            prev_9 = sma9.iloc[-3]
            prev_26 = sma26.iloc[-3]
            
            # شرط تقاطع طلایی: ۹ > ۲۶ امروز و ۹ < ۲۶ دو روز پیش
            if current_9 > current_26 and prev_9 < prev_26:
                info = ticker.info
                last_price = ticker.last_price or 0
                close_price = ticker.adj_close or 0
                price_change = last_price - close_price
                price_change_percent = (price_change / close_price * 100) if close_price else 0
                
                result.append({
                    "symbol": symbol,
                    "name": info.get("name", ""),
                    "group": info.get("group_name", ""),
                    "market": info.get("market", ""),
                    "last_price": last_price,
                    "close_price": close_price,
                    "price_change": price_change,
                    "price_change_percent": round(price_change_percent, 2),
                    "volume": ticker.volume or 0,
                    "value": ticker.value or 0,
                    "sma9": round(current_9, 0),
                    "sma26": round(current_26, 0)
                })
            
            time.sleep(0.5)  # مکث بین درخواست‌ها برای جلوگیری از بلاک شدن
        
        except Exception as e:
            print(f"خطا در {symbol}: {e}")
            continue
    
    return result

def main():
    stocks = get_stocks_with_golden_cross()
    stocks.sort(key=lambda x: x['volume'], reverse=True)
    
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date_shamsi": jdatetime.date.today().strftime("%Y/%m/%d"),
        "stocks": stocks
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(stocks)} نماد با تقاطع طلایی پیدا شد.")

if __name__ == "__main__":
    main()
