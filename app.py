import streamlit as st
import pandas as pd
import yfinance as yf
import os

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V18 完美復刻版", layout="wide")

# ==========================================
# ✨ 視覺美化 CSS 注入 (保持原有色彩與卡片感)
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    div.stColumn > div {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid #e1e8ed;
    }
    h1 { color: #1e3a8a; font-weight: 800; text-align: center; }
    h2, h3 { color: #1e3a8a; font-weight: 700; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800; }
    
    /* 雷達與微笑曲線色彩區塊 */
    .twd-radar { background-color: #eff6ff; border-left: 8px solid #2563eb; padding: 15px; border-radius: 10px; }
    .usd-radar { background-color: #ecfdf5; border-left: 8px solid #059669; padding: 15px; border-radius: 10px; }
    .smile-container { padding: 15px; border-radius: 12px; background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("Sihwa 資本 | 雷恩 40-40-20 旗艦操盤面板 🚀")
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

# 🌐 即時報價看板
st.header("🌐 即時市場脈動")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
col_p1.metric("🔵 00662 (原型)", f"${p_662:.2f}", f"{cp_662:+.2f}%")
col_p2.metric("🔴 00670L (正2)", f"${p_670L:.2f}", f"{cp_670L:+.2f}%")
col_p3.metric("🟩 00865B (保命)", f"${p_865B:.2f}", f"{cp_865B:+.2f}%")
col_p4.metric("💵 USD/TWD", f"${usd_twd:.2f}")

st.markdown("---")

# ==========================================
# 🟡 區塊一：部位管理 (老闆最愛的完整表格)
# ==========================================
st.header("🟡 部位管理與資產配置")

DATA_FILE = "portfolio_data.csv"
CAT_ORDER = ["原型底倉 (00662)", "絕對保命金 (00865B)", "撤退備戰金 (現金)", "原型加碼倉", "正2攻擊 (00670L)"]

if 'shares_data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        _df = pd.read_csv(DATA_FILE)
    else:
        _df = pd.DataFrame({"資產類別": CAT_ORDER, "持有股數或金額": [113000, 150000, 4309152, 0, 0]})
    _df['資產類別'] = pd.Categorical(_df['資產類別'], categories=CAT_ORDER, ordered=True)
    st.session_state.shares_data = _df.sort_values('資產類別').reset_index(drop=True)

df = st.session_state.shares_data.copy()
p_map = {"原型底倉 (00662)": p_662, "絕對保命金 (00865B)": p_865B, "撤退備戰金 (現金)": 1.0, "原型加碼倉": p_662, "正2攻擊 (00670L)": p_670L}
df['今日單價'] = df['資產類別'].map(p_map)
df['市值'] = df['持有股數或金額'] * df['今日單價']
total_val = df['市值'].sum()
df['目前佔比(%)'] = (df['市值'] / total_val * 100) if total_val > 0 else 0
df['目標佔比'] = ["40%", "20%", "0%", "0%", "40%"]

# 損益與 Beta
today_pnl = (df.loc[df['資產類別'].isin(['原型底倉 (00662)', '原型加碼倉']), '持有股數或金額'].sum() * c_662) + \
            (df.loc[df['資產類別'] == '正2攻擊 (00670L)', '持有股數或金額'].sum() * c_670L) + \
            (df.loc[df['資產類別'] == '絕對保命金 (00865B)', '持有股數或金額'].sum() * c_865B)

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 總資產淨值", f"NT$ {total_val:,.0f}")
m2.metric("📊 今日損益", f"NT$ {today_pnl:,.0f}", f"{(today_pnl/total_val)*100:+.2f}%")
m3.metric("🎯 目標 Beta", "1.20")
m4.metric("📈 實質 Beta", f"{((df['市值']/total_val)*[1,0,0,1,2]).sum():.2f}")

# 完整功能表格
edited_df = st.data_editor(
    df[["資產類別", "持有股數或金額", "今日單價", "市值", "目標佔比", "目前佔比(%)"]],
    column_config={
        "持有股數或金額": st.column_config.NumberColumn("✏️ 修改股數/現金", format="%d"),
        "市值": st.column_config.NumberColumn("總市值", format="$%d"),
        "目前佔比(%)": st.column_config.NumberColumn("目前 %", format="%.2f %%"),
    },
    disabled=["資產類別", "今日單價", "市值", "目標佔比", "目前佔比(%)"],
    hide_index=True, use_container_width=True
)

if st.button("💾 儲存最新數據 (存檔後自動重整)"):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.session_state.shares_data.to_csv(DATA_FILE, index=False)
    st.success("✅ 存檔成功！")
    st.rerun()

st.markdown("---")

# ==========================================
# 🔴 區塊二：雙核雷達 (加強現價顯示)
# ==========================================
st.header("🔴 雙核雷達警報系統")
c_r1, c_r2 = st.columns(2)
with c_r1:
    st.markdown('<div class="twd-radar">', unsafe_allow_html=True)
    st.subheader("🇹🇼 00662 監控")
    sma_662 = st.number_input("設定年線基準：", value=93.49, key="n1")
    bias_662 = ((p_662 - sma_662) / sma_662) * 100
    st.metric("00662 現價", f"${p_662:.2f}", f"偏離 {bias_662:.2f}%")
    if bias_662 >= 0: st.success("🟢 安全續抱")
    else: st.error("🔴 跌破年線")
    st.markdown('</div>', unsafe_allow_html=True)

with c_r2:
    st.markdown('<div class="usd-radar">', unsafe_allow_html=True)
    st.subheader("🇺🇸 QQQ 監控")
    sma_qqq = st.number_input("設定 QQQ 年線 (USD)：", value=430.0, key="n2")
    bias_qqq = ((p_qqq - sma_qqq) / sma_qqq) * 100
    st.metric("QQQ 現價", f"${p_qqq:.2f}", f"偏離 {bias_qqq:.2f}%")
    if bias_qqq >= 0: st.success("🟢 美股健康")
    else: st.error("🔴 美股轉弱")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 🔵 區塊三：微笑曲線 (漸層色彩打點)
# ==========================================
st.header("🔵 微笑曲線打點計畫")
cash_reserve = df.loc[df['資產類別'] == '撤退備戰金 (現金)', '市值'].values[0]
st.info(f"💡 目前備戰金： **NT$ {cash_reserve:,.0f}**")

def get_smile_text(label, drop, inv):
    tp = sma_662 * (1 - drop)
    budget = total_val * inv
    shares = int(budget / tp) if tp > 0 else 0
    return f"{label} ➔ **${tp:.2f}** | 買 **{shares:,}** 股 (約 ${budget/10000:.0f}萬)"

drops = [0.08, 0.1, 0.15, 0.2, 0.25, 0.3]
red_colors = ["#fee2e2", "#fecaca", "#fca5a5", "#f87171", "#ef4444", "#dc2626"]
blue_colors = ["#e0f2fe", "#bae6fd", "#7dd3fc", "#38bdf8", "#0ea5e9", "#0284c7"]

cc1, cc2 = st.columns(2)
with cc1:
    st.subheader("📉 下跌段 (5%)")
    for i, d in enumerate(drops):
        st.markdown(f'<div style="background-color:{red_colors[i]}; padding:5px; border-radius:5px; margin-bottom:5px;">', unsafe_allow_html=True)
        st.checkbox(get_smile_text(f"-{d*100:g}%", d, 0.05), key=f"d_{d}")
        st.markdown('</div>', unsafe_allow_html=True)
with cc2:
    st.subheader("📈 反彈段 (2%)")
    for i, d in enumerate(drops):
        st.markdown(f'<div style="background-color:{blue_colors[i]}; padding:5px; border-radius:5px; margin-bottom:5px;">', unsafe_allow_html=True)
        st.checkbox(get_smile_text(f"反彈 {d*100:g}%", d, 0.02), key=f"r_{d}")
        st.markdown('</div>', unsafe_allow_html=True)
