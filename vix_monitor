import os
import requests
import yfinance as yf
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

def monitor_global_risk():
    print("正在抓取全球風險指標...")
    
    # 1. 抓取數據 (VIX, 10年債, 美元, 西德州原油)
    vix_str, vix_val, vix_chg = get_data_info("^VIX", "VIX 恐慌指數")
    tnx_str, tnx_val, tnx_chg = get_data_info("^TNX", "10年美債殖利率")
    dxy_str, dxy_val, dxy_chg = get_data_info("DX-Y.NYB", "美元指數")
    oil_str, oil_val, oil_chg = get_data_info("CL=F", "WTI 原油價格")

    # 2. 綜合風險與市場情緒判斷
    risk_score = 0
    if vix_val > 25: risk_score += 2
    elif vix_val > 20: risk_score += 1
    
    if tnx_chg > 1.5: risk_score += 1 # 債券殖利率大幅跳升
    if dxy_chg > 0.4: risk_score += 1 # 美元走強壓抑台股
    
    status_map = {0: "🟢 市場穩定", 1: "🟡 輕微波動", 2: "🟠 警戒上升", 3: "🔴 高度風險", 4: "🆘 極度恐慌"}
    risk_status = status_map.get(min(risk_score, 4), "🟠 警戒上升")

    # 3. 建立訊息
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

    # 4. 提供台股與航運操作建議
    if risk_score >= 3:
        msg += "\n💡 **建議:** 全球避險情緒高漲，建議今日台股操作以防禦為主，縮小部位。"
    elif oil_chg > 2 and dxy_chg < 0:
        msg += "\n💡 **建議:** 原油走強且美元偏弱，這有利於原物料(散裝)與能源類股，盤面動能強。"
    elif dxy_chg > 0.5:
        msg += "\n💡 **建議:** 美元異常強勢，注意外資對權值股的調節壓力。"
    else:
        msg += "\n💡 **建議:** 盤勢平穩，適合回歸個股籌碼分析與 BDI 趨勢操作。"

    # 5. 發送通知
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})
        print("全球風險報告已發送")

if __name__ == "__main__":
    monitor_global_risk()
