import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V6 旗艦投資儀表板", layout="wide")
st.title("Sihwa 資本 | 雷恩 40-40-20 旗艦儀表板 🚀")
st.markdown("---")

# 1. 設定自動抓取資料工具 (含 % 漲跌計算)
@st.cache_data(ttl=900)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            current = hist['Close'].iloc[-1]
            change = current - prev_close
            change_pct = (change / prev_close) * 100
            return float(current), float(change), float(change_pct)
        else:
            current = hist['Close'].iloc[-1]
            return float(current), 0.0, 0.0
    except:
        return 100.0, 0.0, 0.0

# 2. 抓取匯率
@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        rate = yf.Ticker("USDTWD=X").history(period="1d")['Close'].iloc[-1]
        return float(rate)
    except:
        return 32.5

# ==========================================
# 頂部即時看盤區 (加入 % 漲跌)
# ==========================================
st.header("📡 系統連線：即時報價與匯率")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)

with st.spinner('數據同步中...'):
    p_662, c_662, cp_662 = get_stock_data("00662.TW")
    p_670L, c_670L, cp_670L = get_stock_data("00670L.TW")
    p_865B, c_865B, cp_865B = get_stock_data("00865B.TW")
    usd_twd = get_exchange_rate()

col_p1.metric("原型底倉 (00662A)", f"${p_662:.2f}", f"{c_662:+.2f} ({cp_662:+.2f}%)")
col_p2.metric("正2攻擊 (00670L)", f"${p_670L:.2f}", f"{c_670L:+.2f} ({cp_670L:+.2f}%)")
col_p3.metric("絕對保命金 (00865B)", f"${p_865B:.2f}", f"{c_865B:+.2f} ({cp_865B:+.2f}%)")
col_p4.metric("USD/TWD 匯率", f"${usd_twd:.2f}")

st.markdown("---")
# ==========================================
# 區塊一：資產配置與 Beta 監控
# ==========================================
st.header("🟡 區塊一：部位管理與 Beta 風險控管")

if 'shares_data' not in st.session_state:
    st.session_state.shares_data = pd.DataFrame({
        "資產類別": ["原型底倉 (00662A)", "原型加碼倉", "正2攻擊 (00670L)", "絕對保命金 (00865B)", "撤退備戰金 (現金)"],
        "持有股數或金額": [113000, 10000, 5000000, 150000, 4309152],
        "個股Beta": [1.0, 1.0, 2.0, 0.0, 0.0]
    })

# 計算市值
df = st.session_state.shares_data.copy()
df['今日單價'] = [p_662, p_662, p_670L, p_865B, 1.0]
df['市值'] = df['持有股數或金額'] * df['今日單價']
total_val = df['市值'].sum()
df['佔比'] = (df['市值'] / total_val)

# [重點] 計算 Beta
current_beta = (df['佔比'] * df['個股Beta']).sum()
target_beta = 1.20  # 雷恩 40-40-20 的標準 Beta

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("💰 目前總資產淨值", f"NT$ {total_val:,.0f}")
col_m2.metric("🎯 目標總 Beta", f"{target_beta:.2f}")
col_m3.metric("📈 目前實質 Beta", f"{current_beta:.2f}", f"{current_beta - target_beta:+.2f}", delta_color="inverse")

# 顯示表格
df['佔比(%)'] = df['佔比'].apply(lambda x: f"{x*100:.2f}%")
edited_df = st.data_editor(
    df[["資產類別", "持有股數或金額", "今日單價", "市值", "佔比(%)", "個股Beta"]],
    column_config={"市值": st.column_config.NumberColumn(format="$%d")},
    disabled=["資產類別", "今日單價", "市值", "佔比(%)", "個股Beta"],
    hide_index=True, use_container_width=True
)

if not edited_df['持有股數或金額'].equals(st.session_state.shares_data['持有股數或金額']):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.rerun()

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達 (年線監控)
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器")
sma_240 = st.number_input("請輸入 00662A 目前的 240日年線：", value=93.49, step=0.1)
bias = ((p_662 - sma_240) / sma_240) * 100
st.metric(label="00662A 距離年線偏離率", value=f"{bias:.2f}%", delta="安全續抱" if bias > 0 else "空頭警訊")

st.markdown("---")
# ==========================================
# 區塊三：微笑曲線 (精簡精算版)
# ==========================================
st.header("🔵 區塊三：微笑曲線分批買入計畫表")
cash_reserve = df.loc[df['資產類別'] == '撤退備戰金 (現金)', '市值'].values[0]
st.write(f"💡 目前可動用現金： **NT$ {cash_reserve:,.0f}**")

def calc_smile_row(drop_rate, invest_ratio):
    trigger_p = sma_240 * (1 - drop_rate)
    budget = total_val * invest_ratio
    shares = int(budget / trigger_p) if trigger_p > 0 else 0
    return [f"{drop_rate*100:g}%", f"${trigger_p:.2f}", f"${budget:,.0f}", f"{shares:,} 股"]

# 建立計畫表數據
smile_data = []
for drop, inv in [(0.08, 0.05), (0.1, 0.05), (0.15, 0.05), (0.2, 0.05), (0.25, 0.05), (0.3, 0.05)]:
    smile_data.append(calc_smile_row(drop, inv))

smile_df = pd.DataFrame(smile_data, columns=["跌幅觸發", "觸發價格", "預計動用金額", "建議買入股數"])
st.table(smile_df) # 使用 table 讓畫面更精簡好看

st.error("🛑 提示：若跌幅超過 -30%，請停止任何加碼動作，保留現金冬眠！")
