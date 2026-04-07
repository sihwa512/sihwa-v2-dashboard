import streamlit as st
import pandas as pd
import yfinance as yf
import os

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V16 數據精簡版", layout="wide")
st.title("Sihwa 資本 | 雷恩 40-40-20 旗艦儀表板 🚀")
st.markdown("---")

# 1. 數據抓取工具
@st.cache_data(ttl=600)
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
        return float(hist['Close'].iloc[-1]), 0.0, 0.0
    except:
        return 100.0, 0.0, 0.0

@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        return float(yf.Ticker("USDTWD=X").history(period="1d")['Close'].iloc[-1])
    except:
        return 32.5

# 數據同步
with st.spinner('市場數據同步中...'):
    p_662, c_662, cp_662 = get_stock_data("00662.TW")
    p_670L, c_670L, cp_670L = get_stock_data("00670L.TW")
    p_865B, c_865B, cp_865B = get_stock_data("00865B.TW")
    p_qqq, c_qqq, cp_qqq = get_stock_data("QQQ")
    usd_twd = get_exchange_rate()

# 頂部即時看板
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
col_p1.metric("00662 (原型)", f"${p_662:.2f}", f"{cp_662:+.2f}%")
col_p2.metric("00670L (正2)", f"${p_670L:.2f}", f"{cp_670L:+.2f}%")
col_p3.metric("00865B (保命)", f"${p_865B:.2f}", f"{cp_865B:+.2f}%")
col_p4.metric("USD/TWD 匯率", f"${usd_twd:.2f}")

st.markdown("---")

# ==========================================
# 區塊一：部位管理
# ==========================================
st.header("🟡 區塊一：部位管理與 Beta 監控")

DATA_FILE = "portfolio_data.csv"
CAT_ORDER = ["原型底倉 (00662)", "絕對保命金 (00865B)", "撤退備戰金 (現金)", "原型加碼倉", "正2攻擊 (00670L)"]

if 'shares_data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        _df = pd.read_csv(DATA_FILE)
    else:
        _df = pd.DataFrame({
            "資產類別": CAT_ORDER,
            "持有股數或金額": [113000, 150000, 4309152, 0, 0]
        })
    _df['資產類別'] = _df['資產類別'].replace("原型底倉 (00662A)", "原型底倉 (00662)")
    _df['資產類別'] = pd.Categorical(_df['資產類別'], categories=CAT_ORDER, ordered=True)
    st.session_state.shares_data = _df.sort_values('資產類別').reset_index(drop=True)

df = st.session_state.shares_data.copy()

p_map = {"原型底倉 (00662)": p_662, "絕對保命金 (00865B)": p_865B, "撤退備戰金 (現金)": 1.0, "原型加碼倉": p_662, "正2攻擊 (00670L)": p_670L}
b_map = {"原型底倉 (00662)": 1.0, "絕對保命金 (00865B)": 0.0, "撤退備戰金 (現金)": 0.0, "原型加碼倉": 1.0, "正2攻擊 (00670L)": 2.0}
t_map = {"原型底倉 (00662)": "40%", "絕對保命金 (00865B)": "20%", "撤打退戰金 (現金)": "0%", "原型加碼倉": "0%", "正2攻擊 (00670L)": "40%"}

df['今日報價'] = df['資產類別'].map(p_map)
df['市值'] = df['持有股數或金額'] * df['今日報價']
total_val = df['市值'].sum()
# 將目前佔比轉為 0-100 的百分比數值
df['目前佔比(%)'] = (df['市值'] / total_val * 100) if total_val > 0 else 0
df['目標佔比'] = df['資產類別'].map(t_map)
df['個股Beta'] = df['資產類別'].map(b_map)

today_pnl = (df.loc[df['資產類別'].isin(['原型底倉 (00662)', '原型加碼倉']), '持有股數或金額'].sum() * c_662) + \
            (df.loc[df['資產類別'] == '正2攻擊 (00670L)', '持有股數或金額'].sum() * c_670L) + \
            (df.loc[df['資產類別'] == '絕對保命金 (00865B)', '持有股數或金額'].sum() * c_865B)
current_beta = ((df['目前佔比(%)'] / 100) * df['個股Beta']).sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 總資產淨值", f"NT$ {total_val:,.0f}")
m2.metric("📊 今日總損益", f"NT$ {today_pnl:,.0f}", f"{(today_pnl/total_val)*100:+.2f}%")
m3.metric("🎯 目標 Beta", "1.20")
m4.metric("📈 實質 Beta", f"{current_beta:.2f}", f"{current_beta-1.2:.2f}", delta_color="inverse")

# 調整表格設定，改為百分比格式
edited_df = st.data_editor(
    df[["資產類別", "持有股數或金額", "今日報價", "市值", "目標佔比", "目前佔比(%)"]],
    column_config={
        "持有股數或金額": st.column_config.NumberColumn("✏️ 持有股數或現金", format="%d", step=1),
        "市值": st.column_config.NumberColumn("總市值", format="$%d"),
        "目前佔比(%)": st.column_config.NumberColumn("📊 目前佔比", format="%.2f %%"),
    },
    disabled=["資產類別", "今日報價", "市值", "目標佔比", "目前佔比(%)"],
    hide_index=True, use_container_width=True
)

if st.button("💾 儲存最新數據"):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.session_state.shares_data.to_csv(DATA_FILE, index=False)
    st.success("存檔成功！")
    st.rerun()

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器")

c_r1, c_r2 = st.columns(2)
with c_r1:
    st.subheader("🇹🇼 00662 監控")
    sma_662 = st.number_input("輸入 00662 年線設定：", value=93.49)
    bias_662 = ((p_662 - sma_662) / sma_662) * 100
    
    col_v1, col_v2 = st.columns(2)
    col_v1.metric("00662 現在股價", f"${p_662:.2f}")
    col_v2.metric("00662 偏離率", f"{bias_662:.2f}%", "安全" if bias_662>0 else "跌破")

with c_r2:
    st.subheader("🇺🇸 QQQ 監控")
    sma_qqq = st.number_input("輸入 QQQ 年線設定 (USD)：", value=430.0)
    bias_qqq = ((p_qqq - sma_qqq) / sma_qqq) * 100
    
    col_v3, col_v4 = st.columns(2)
    col_v3.metric("QQQ 現在股價", f"${p_qqq:.2f}")
    col_v4.metric("QQQ 偏離率", f"{bias_qqq:.2f}%", "安全" if bias_qqq>0 else "跌破")

st.markdown("---")
# ==========================================
# 區塊三：微笑曲線
# ==========================================
st.header("🔵 區塊三：微笑曲線打點計畫")
cash_reserve = df.loc[df['資產類別'] == '撤退備戰金 (現金)', '市值'].values[0]
st.write(f"💡 目前備戰金： **NT$ {cash_reserve:,.0f}**")

def get_smile_text(label, drop, inv):
    tp = sma_662 * (1 - drop)
    budget = total_val * inv
    shares = int(budget / tp) if tp > 0 else 0
    return f"{label} ➔ 觸發價 **${tp:.2f}** | 買 **{shares:,}** 股 (約 ${budget/10000:.0f}萬)"

cc1, cc2 = st.columns(2)
with cc1:
    st.subheader("📉 下跌段 (5%)")
    for d in [0.08, 0.1, 0.15, 0.2, 0.25, 0.3]:
        st.checkbox(get_smile_text(f"-{d*100:g}%", d, 0.05))
with cc2:
    st.subheader("📈 反彈段 (2%)")
    for d in [0.08, 0.1, 0.15, 0.2, 0.25, 0.3]:
        st.checkbox(get_smile_text(f"反彈 {d*100:g}%", d, 0.02))
