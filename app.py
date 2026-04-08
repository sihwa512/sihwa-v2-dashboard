import streamlit as st
import pandas as pd
import yfinance as yf
import os

# 設定網頁標題與寬版顯示 (並注入手機優化 CSS)
st.set_page_config(page_title="Sihwa 資本 - V19 行動優先版", layout="wide")

st.markdown("""
    <style>
    /* 全域字體縮放與邊距優化 */
    .stApp { background-color: #f4f7f6; }
    
    /* 針對手機版調整 Metric 字體 */
    [data-testid="stMetricValue"] {
        font-size: calc(1.5rem + 1vw) !important;
        font-weight: 800;
    }
    
    /* 卡片樣式強化 */
    div.stColumn > div {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        margin-bottom: 15px;
        border: 1px solid #eef2f3;
    }
    
    /* 微笑曲線美化 */
    .smile-card {
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }

    /* 隱藏 Streamlit 預設的多餘間距 */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("Sihwa 資本 | 行動操盤儀表板 📱")

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
with st.spinner('連線中...'):
    p_662, c_662, cp_662 = get_stock_data("00662.TW")
    p_670L, c_670L, cp_670L = get_stock_data("00670L.TW")
    p_865B, c_865B, cp_865B = get_stock_data("00865B.TW")
    p_qqq, c_qqq, cp_qqq = get_stock_data("QQQ")
    usd_twd = get_exchange_rate()

# ==========================================
# 🌐 即時報價 (手機會自動轉為多行)
# ==========================================
col_p1, col_p2 = st.columns(2)
col_p1.metric("00662 (原型)", f"${p_662:.2f}", f"{cp_662:+.2f}%")
col_p2.metric("00670L (正2)", f"${p_670L:.2f}", f"{cp_670L:+.2f}%")

col_p3, col_p4 = st.columns(2)
col_p3.metric("00865B (保命)", f"${p_865B:.2f}", f"{cp_865B:+.2f}%")
col_p4.metric("USD/TWD", f"${usd_twd:.2f}")

st.markdown("---")

# ==========================================
# 🟡 區塊一：部位管理 (精簡手機版)
# ==========================================
st.subheader("🟡 部位與資產淨值")

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
df['今日報價'] = df['資產類別'].map(p_map)
df['市值'] = df['持有股數或金額'] * df['今日報價']
total_val = df['市值'].sum()
df['目前 %'] = (df['市值'] / total_val * 100) if total_val > 0 else 0

# 損益計算
today_pnl = (df.loc[df['資產類別'].isin(['原型底倉 (00662)', '原型加碼倉']), '持有股數或金額'].sum() * c_662) + \
            (df.loc[df['資產類別'] == '正2攻擊 (00670L)', '持有股數或金額'].sum() * c_670L) + \
            (df.loc[df['資產類別'] == '絕對保命金 (00865B)', '持有股數或金額'].sum() * c_865B)

st.metric("總資產淨值", f"NT$ {total_val:,.0f}")
st.metric("今日總損益", f"NT$ {today_pnl:,.0f}", f"{(today_pnl/total_val)*100:+.2f}%")

# 手機版表格：移除多餘欄位，只留精華
edited_df = st.data_editor(
    df[["資產類別", "持有股數或金額", "市值", "目前 %"]],
    column_config={
        "持有股數或金額": st.column_config.NumberColumn("✏️ 數量", format="%d"),
        "市值": st.column_config.NumberColumn("市值", format="$%d"),
        "目前 %": st.column_config.NumberColumn("%", format="%.1f%%"),
    },
    disabled=["資產類別", "市值", "目前 %"],
    hide_index=True, use_container_width=True
)

if st.button("💾 儲存最新數據並重整", use_container_width=True):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.session_state.shares_data.to_csv(DATA_FILE, index=False)
    st.rerun()

st.markdown("---")

# ==========================================
# 🔴 區塊二：雷達 (卡片對齊)
# ==========================================
st.subheader("🔴 雙核防禦雷達")
sma_662 = st.number_input("00662 年線：", value=93.49)
bias_662 = ((p_662 - sma_662) / sma_662) * 100

cr1, cr2 = st.columns(2)
cr1.metric("00662 現價", f"${p_662:.2f}")
cr2.metric("00662 偏離", f"{bias_662:.2f}%", delta_color="normal" if bias_662>0 else "inverse")

if bias_662 >= 0: st.success("🟢 安全續抱")
elif bias_662 >= -3: st.warning("🟡 警戒觀察")
else: st.error("🔴 清空正2！")

st.markdown("---")

# ==========================================
# 🔵 區塊三：微笑曲線 (手機 Tabs 切換版)
# ==========================================
st.subheader("🔵 微笑曲線計畫")
tab1, tab2 = st.tabs(["📉 下跌段", "📈 反彈段"])

def get_smile_text(label, drop, inv):
    tp = sma_662 * (1 - drop)
    budget = total_val * inv
    shares = int(budget / tp) if tp > 0 else 0
    return f"觸發 **${tp:.2f}** | 買 **{shares:,}** 股"

drops = [0.08, 0.1, 0.15, 0.2, 0.25, 0.3]
red_shades = ["#fee2e2", "#fecaca", "#fca5a5", "#f87171", "#ef4444", "#dc2626"]
blue_shades = ["#e0f2fe", "#bae6fd", "#7dd3fc", "#38bdf8", "#0ea5e9", "#0284c7"]

with tab1:
    for i, d in enumerate(drops):
        st.markdown(f'<div class="smile-card" style="background-color:{red_shades[i]};">', unsafe_allow_html=True)
        st.checkbox(f"-{d*100:g}% ({get_smile_text('', d, 0.05)})", key=f"d_{d}")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    for i, d in enumerate(drops):
        st.markdown(f'<div class="smile-card" style="background-color:{blue_shades[i]};">', unsafe_allow_html=True)
        st.checkbox(f"反彈 {d*100:g}% ({get_smile_text('', d, 0.02)})", key=f"r_{d}")
        st.markdown('</div>', unsafe_allow_html=True)

st.error("🛑 跌破 -30% 停止加碼冬眠！")
