import os
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# 從 GitHub Secrets 讀取 Webhook
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def get_data_info(symbol, name):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="5d")
    if df.empty: return f"{name}: 獲取失敗", 0, 0
    
    last_val = df['Close'].iloc[-1]
    prev_val = df['Close'].iloc[-2]
    change = ((last_val - prev_val) / prev_val) * 100
    return f"{name}: {last_val:.2f} ({change:+.2f}%)", last_val, change

def get_fear_and_greed():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://edition.cnn.com",
        "Referer": "https://edition.cnn.com/"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        score = int(data["fear_and_greed"]["score"])
        rating = data["fear_and_greed"]["rating"]
        
        rating_map = {
            "extreme fear": "極度恐慌",
            "fear": "恐慌",
            "neutral": "中立",
            "greed": "貪婪",
            "extreme greed": "極度貪婪"
        }
        return score, rating_map.get(rating.lower(), rating.title())
    except Exception:
        return None, "獲取失敗"

def generate_trend_chart():
    print("正在生成近半年走勢圖...")
    tickers = {
        "^VIX": "VIX Index",
        "^TNX": "10Y Treasury Yield",
        "DX-Y.NYB": "US Dollar Index (DXY)",
        "CL=F": "WTI Crude Oil"
    }
    
    fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
    fig.suptitle(f"Global Risk Indicators (Last 6 Months) - {datetime.now().strftime('%Y-%m-%d')}", fontsize=16)
    
    for ax, (symbol, name) in zip(axs, tickers.items()):
        try:
            df = yf.Ticker(symbol).history(period="6mo")
            if not df.empty:
                ax.plot(df.index, df['Close'], label=name, color='#1f77b4')
                ax.set_ylabel("Price / Yield")
                ax.legend(loc="upper left")
                ax.grid(True, linestyle='--', alpha=0.6)
        except Exception as e:
            print(f"無法繪製 {name}: {e}")
            
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    chart_filename = "risk_chart.png"
    plt.savefig(chart_filename)
    plt.close()
    return chart_filename

def monitor_global_risk():
    print("正在抓取全球風險指標...")
    
    vix_str, vix_val, vix_chg = get_data_info("^VIX", "VIX 恐慌指數")
    tnx_str, tnx_val, tnx_chg = get_data_info("^TNX", "10年美債殖利率")
    dxy_str, dxy_val, dxy_chg = get_data_info("DX-Y.NYB", "美元指數")
    oil_str, oil_val, oil_chg = get_data_info("CL=F", "WTI 原油價格")
    
    fg_score, fg_rating = get_fear_and_greed()
    fg_str = f"CNN 恐慌貪婪: {fg_score} ({fg_rating})" if fg_score is not None else f"CNN 恐慌貪婪: {fg_rating}"

    # 綜合風險分數判斷
    risk_score = 0
    if vix_val > 25: risk_score += 2
    elif vix_val > 20: risk_score += 1
    
    if fg_score is not None and fg_score <= 25: risk_score += 1
    if tnx_chg > 1.5: risk_score += 1
    if dxy_chg > 0.4: risk_score += 1
    
    status_map = {0: "🟢 市場穩定", 1: "🟡 輕微波動", 2: "🟠 警戒上升", 3: "🔴 高度風險", 4: "🆘 極度恐慌"}
    risk_status = status_map.get(min(risk_score, 4), "🟠 警戒上升")

    # 建立文字訊息頭部
    msg = (
        f"🌍 **全球金融壓力監控 (美股收盤)**\n"
        f"📅 日期: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"---"
        f"\n⚠️ **{vix_str}**"
        f"\n🧭 **{fg_str}**"
        f"\n📈 **{tnx_str}**"
        f"\n💵 **{dxy_str}**"
        f"\n🛢️ **{oil_str}**"
        f"\n---"
        f"\n🛡️ 綜合風險狀態: **{risk_status}**\n"
    )

    # 策略判斷 (回歸原本簡潔的條件判斷，並整合 F&G 與關注資產)
    suggestions = []
    
    # 1. 總體風險與情緒 (VIX 與 F&G)
    if risk_score >= 3 or (fg_score is not None and fg_score <= 25):
        suggestions.append("全球避險情緒與恐慌指數高漲，建議今日台股操作以防禦為主，縮小部位。")
    elif fg_score is not None and fg_score >= 75:
        suggestions.append("市場情緒極度貪婪，留意熱門股與大盤的獲利了結賣壓，適度提高現金水位。")
        
    # 2. 利率環境 (TNX)
    if tnx_chg > 1.5:
        suggestions.append("美債殖利率急升，特別股、ETD 等對利率敏感的資產估值將承受壓力。")
    elif tnx_chg < -1.0:
        suggestions.append("美債殖利率回落，有利於 ETD、可轉債 (CB) 等固定收益型資產表現。")
        
    # 3. 匯率與原物料 (DXY 與 WTI)
    if oil_chg > 2 and dxy_chg < 0:
        suggestions.append("原油走強且美元偏弱，有利於原物料 (散裝航運) 與能源類股，盤面動能強。")
    elif dxy_chg > 0.5:
        suggestions.append("美元異常強勢，注意外資對台股大型權值股的調節提款壓力。")
        
    # 4. 預設平穩狀態
    if not suggestions:
        suggestions.append("盤勢平穩，適合回歸個股籌碼分析與 BDI 趨勢操作。")

    # 將建議附加到訊息中
    for s in suggestions:
        msg += f"\n💡 **建議:** {s}"

    # 生成圖表
    chart_path = generate_trend_chart()

    # 發送通知
    if DISCORD_WEBHOOK_URL:
        try:
            with open(chart_path, "rb") as f:
                response = requests.post(
                    DISCORD_WEBHOOK_URL, 
                    data={"content": msg},
                    files={"file": (chart_path, f, "image/png")}
                )
                
            if response.status_code in [200, 204]:
                print("全球風險報告與圖表已發送")
            else:
                print(f"發送失敗，狀態碼: {response.status_code}, 回應: {response.text}")
                
        except Exception as e:
            print(f"Webhook 發送發生錯誤: {e}")

if __name__ == "__main__":
    monitor_global_risk()
