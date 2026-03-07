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

def generate_trend_chart():
    """抓取過去 6 個月的資料並生成走勢圖"""
    print("正在生成近半年走勢圖...")
    tickers = {
        "^VIX": "VIX Index",
        "^TNX": "10Y Treasury Yield",
        "DX-Y.NYB": "US Dollar Index (DXY)",
        "CL=F": "WTI Crude Oil"
    }
    
    # 建立 4 個子圖
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
            
    plt.tight_layout(rect=[0, 0.03, 1, 0.97]) # 避免標題與圖表重疊
    
    chart_filename = "risk_chart.png"
    plt.savefig(chart_filename)
    plt.close()
    return chart_filename

def monitor_global_risk():
    print("正在抓取全球風險指標...")
    
    # 1. 抓取數據
    vix_str, vix_val, vix_chg = get_data_info("^VIX", "VIX 恐慌指數")
    tnx_str, tnx_val, tnx_chg = get_data_info("^TNX", "10年美債殖利率")
    dxy_str, dxy_val, dxy_chg = get_data_info("DX-Y.NYB", "美元指數")
    oil_str, oil_val, oil_chg = get_data_info("CL=F", "WTI 原油價格")

    # 2. 綜合風險與市場情緒判斷
    risk_score = 0
    if vix_val > 25: risk_score += 2
    elif vix_val > 20: risk_score += 1
    
    if tnx_chg > 1.5: risk_score += 1
    if dxy_chg > 0.4: risk_score += 1
    
    status_map = {0: "🟢 市場穩定", 1: "🟡 輕微波動", 2: "🟠 警戒上升", 3: "🔴 高度風險", 4: "🆘 極度恐慌"}
    risk_status = status_map.get(min(risk_score, 4), "🟠 警戒上升")

    # 3. 建立文字訊息
    msg = (
        f"🌍 **全球金融壓力監控 (美股收盤)**\n"
        f"📅 日期: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"---"
        f"\n⚠️ **{vix_str}**"
        f"\n📈 **{tnx_str}**"
        f"\n💵 **{dxy_str}**"
        f"\n🛢️ **{oil_str}**"
        f"\n---"
        f"\n🛡️ 綜合風險狀態: **{risk_status}**"
    )

    if risk_score >= 3:
        msg += "\n💡 **建議:** 全球避險情緒高漲，建議今日台股操作以防禦為主，縮小部位。"
    elif oil_chg > 2 and dxy_chg < 0:
        msg += "\n💡 **建議:** 原油走強且美元偏弱，有利於原物料(散裝)與能源類股，盤面動能強。"
    elif dxy_chg > 0.5:
        msg += "\n💡 **建議:** 美元異常強勢，注意外資對權值股的調節壓力。"
    else:
        msg += "\n💡 **建議:** 盤勢平穩，適合回歸個股籌碼分析與 BDI 趨勢操作。"

    # 4. 生成圖表
    chart_path = generate_trend_chart()

    # 5. 發送通知 (包含圖片)
    if DISCORD_WEBHOOK_URL:
        try:
            with open(chart_path, "rb") as f:
                # 傳送圖片給 Discord 必須改用 data 傳遞文字，files 傳遞圖片
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
