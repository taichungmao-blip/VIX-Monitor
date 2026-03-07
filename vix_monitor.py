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

def get_market_strategy(vix_val, tnx_chg, dxy_chg, oil_chg):
    """根據四大指標變動，產生板塊輪動與交易策略建議"""
    buy_sectors = []
    avoid_sectors = []
    notes = []

    # 1. VIX 判斷 (市場恐慌度)
    if vix_val > 25:
        buy_sectors.append("防禦型標的 (如公用事業)、現金部位")
        avoid_sectors.append("高 Beta 科技股、中小型股")
        notes.append("VIX 處於高位，系統性風險增加，建議降低整體持股水位。")
    elif vix_val < 15:
        buy_sectors.append("科技成長股、可轉債 (CB)")
        notes.append("市場情緒穩定，有利於股權資產與可轉債發揮選擇權價值。")

    # 2. TNX 判斷 (利率環境)
    if tnx_chg > 1.5:  
        buy_sectors.append("金融股")
        avoid_sectors.append("REITs、ETD、特別股")
        notes.append("美債殖利率急升，對長天期與固定收益型資產估值造成壓力。")
    elif tnx_chg < -1.0: 
        buy_sectors.append("REITs、ETD、高息低波股")
        notes.append("殖利率回落，有利於固定收益型與對利率敏感的資產反彈。")

    # 3. DXY 判斷 (資金流向)
    if dxy_chg > 0.5:
        avoid_sectors.append("新興市場股市 (含台股權值股)")
        notes.append("美元走強，外資匯出壓力大，台股大型權值股易成提款機。")
    elif dxy_chg < -0.5:
        buy_sectors.append("新興市場股市、原物料")
        notes.append("美元弱勢，資金有利於回流亞洲新興市場。")

    # 4. WTI 判斷 (通膨與能源)
    if oil_chg > 2.0:
        buy_sectors.append("能源類股、塑化原料")
        avoid_sectors.append("航空、運輸")
        notes.append("油價強勢推升通膨預期，同時壓縮運輸業獲利空間。")
    
    # 若皆無明顯波動的預設狀態
    if not buy_sectors and not avoid_sectors:
        buy_sectors.append("回歸個股基本面與籌碼面")
        avoid_sectors.append("無明顯弱勢板塊")
        notes.append("四大指標無劇烈波動，大盤進入震盪整理或緩步墊高格局。")

    # 移除重複項目並轉為字串
    buy_str = "、".join(list(dict.fromkeys(buy_sectors)))
    avoid_str = "、".join(list(dict.fromkeys(avoid_sectors)))
    notes_str = "\n".join([f"🔹 {n}" for n in notes])
    
    return buy_str, avoid_str, notes_str

def monitor_global_risk():
    print("正在抓取全球風險指標...")
    
    vix_str, vix_val, vix_chg = get_data_info("^VIX", "VIX 恐慌指數")
    tnx_str, tnx_val, tnx_chg = get_data_info("^TNX", "10年美債殖利率")
    dxy_str, dxy_val, dxy_chg = get_data_info("DX-Y.NYB", "美元指數")
    oil_str, oil_val, oil_chg = get_data_info("CL=F", "WTI 原油價格")

    # 綜合風險狀態判斷
    risk_score = 0
    if vix_val > 25: risk_score += 2
    elif vix_val > 20: risk_score += 1
    if tnx_chg > 1.5: risk_score += 1
    if dxy_chg > 0.4: risk_score += 1
    
    status_map = {0: "🟢 市場穩定", 1: "🟡 輕微波動", 2: "🟠 警戒上升", 3: "🔴 高度風險", 4: "🆘 極度恐慌"}
    risk_status = status_map.get(min(risk_score, 4), "🟠 警戒上升")

    # 取得策略建議
    buy_str, avoid_str, notes_str = get_market_strategy(vix_val, tnx_chg, dxy_chg, oil_chg)

    # 建立 Discord 文字訊息
    msg = (
        f"🌍 **全球金融壓力監控 (美股收盤)**\n"
        f"📅 日期: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"---"
        f"\n⚠️ **{vix_str}**"
        f"\n📈 **{tnx_str}**"
        f"\n💵 **{dxy_str}**"
        f"\n🛢️ **{oil_str}**"
        f"\n---"
        f"\n🛡️ 綜合風險狀態: **{risk_status}**\n\n"
        f"💡 **板塊與策略建議**\n"
        f"✅ **建議關注 / 買進**: {buy_str}\n"
        f"❌ **建議避開 / 減碼**: {avoid_str}\n\n"
        f"📝 **市場觀察**:\n{notes_str}"
    )

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
