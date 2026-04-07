import streamlit as st
import pandas as pd
import yfinance as yf
import os

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V8 雙重雷達儀表板", layout="wide")
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
# 頂部即時看盤區
# ==========================================
st.header("📡 系統連線：即時報價與匯率")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)

with st.spinner('數據同步中...'):
    p_662, c_662, cp_662 = get_stock_data("00662.TW")
    p_670L, c_670L, cp_670L = get_stock_data("00670L.TW")
    p_865B, c_865B, cp_865B = get_stock_data("00865B.TW")
    p_qqq, c_qqq, cp_qqq = get_stock_data("QQQ") # 新增抓取美股 QQQ
    usd_twd = get_exchange_rate()

col_p1.metric("原型底倉 (00662A)", f"${p_662:.2f}", f"{c_662:+.2f} ({cp_662:+.2f}%)")
col_p2.metric("正2攻擊 (00670L)", f"${p_670L:.2f}", f"{c_670L:+.2f} ({cp_670L:+.2f}%)")
col_p3.metric("絕對保命金 (00865B)", f"${p_865B:.2f}", f"{c_865B:+.2f} ({cp_865B:+.2f}%)")
col_p4.metric("USD/TWD 匯率", f"${usd_twd:.2f}")

st.markdown("---")
# ==========================================
# 區塊一：部位管理、損益與 Beta
# ==========================================
st.header("🟡 區塊一：部位管理與 Beta 風險控管")

DATA_FILE = "portfolio_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame({
            "資產類別": ["原型底倉 (00662A)", "原型加碼倉", "正2攻擊 (00670L)", "絕對保命金 (00865B)", "撤退備戰金 (現金)"],
            "持有股數或金額": [113000, 0, 0, 150000, 4309152],
            "個股Beta": [1.0, 1.0, 2.0, 0.0, 0.0]
        })

if 'shares_data' not in st.session_state:
    st.session_state.shares_data = load_data()

df = st.session_state.shares_data.copy()
df['今日單價'] = [p_662, p_662, p_670L, p_865B, 1.0]
df['市值'] = df['持有股數或金額'] * df['今日單價']
total_val = df['市值'].sum()
df['佔比'] = (df['市值'] / total_val) if total_val > 0 else 0

qty_662_base = df.loc[0, '持有股數或金額']
qty_662_add = df.loc[1, '持有股數或金額']
qty_670L = df.loc[2, '持有股數或金額']
qty_865B = df.loc[3, '持有股數或金額']
today_pnl = (qty_662_base * c_662) + (qty_662_add * c_662) + (qty_670L * c_670L) + (qty_865B * c_865B)

current_beta = (df['佔比'] * df['個股Beta']).sum()
target_beta = 1.20

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("💰 目前總資產淨值", f"NT$ {total_val:,.0f}")
col_m2.metric("📊 今日總損益", f"NT$ {today_pnl:,.0f}", f"{(today_pnl/total_val)*100:+.2f}%" if total_val > 0 else "0.00%")
col_m3.metric("🎯 目標總 Beta", f"{target_beta:.2f}")
col_m4.metric("📈 目前實質 Beta", f"{current_beta:.2f}", f"{current_beta - target_beta:+.2f}", delta_color="inverse")

df['佔比(%)'] = df['佔比'].apply(lambda x: f"{x*100:.2f}%")
edited_df = st.data_editor(
    df[["資產類別", "持有股數或金額", "今日單價", "市值", "佔比(%)", "個股Beta"]],
    column_config={"市值": st.column_config.NumberColumn(format="$%d")},
    disabled=["資產類別", "今日單價", "市值", "佔比(%)", "個股Beta"],
    hide_index=True, use_container_width=True
)

col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("💾 儲存最新股數", use_container_width=True):
        st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
        st.session_state.shares_data.to_csv(DATA_FILE, index=False)
        st.success("✅ 儲存成功！下次將自動載入此設定。")
        st.rerun()

if not edited_df['持有股數或金額'].equals(st.session_state.shares_data['持有股數或金額']):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.rerun()

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達 (00662A & QQQ 雙重監控)
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器 (台美雙指標監控)")
col_r1, col_r2, col_r3 = st.columns(3)

with col_r1:
    sma_240 = st.number_input("00662A 240日年線：", value=93.49, step=0.1)
    bias_662 = ((p_662 - sma_240) / sma_240) * 100
    st.metric(label="00662A 偏離率", value=f"{bias_662:.2f}%", delta="安全" if bias_662 > 0 else "跌破")

with col_r2:
    qqq_sma_240 = st.number_input("QQQ 240日年線 (USD)：", value=430.0, step=0.5)
    bias_qqq = ((p_qqq - qqq_sma_240) / qqq_sma_240) * 100
    # 在標題偷偷塞入 QQQ 現價供參考
    st.metric(label=f"QQQ 偏離率 (現價 ${p_qqq:.2f})", value=f"{bias_qqq:.2f}%", delta="安全" if bias_qqq > 0 else "跌破")

with col_r3:
    st.markdown("<br>", unsafe_allow_html=True) # 排版對齊用
    if bias_662 >= 0:
        st.success("🟩 系統判定：安全，持股續抱")
    elif bias_662 >= -3:
        st.warning("🟨 系統判定：警戒，觀察是否連續三日站不回")
    else:
        st.error("🟥 系統判定：危險撤退，清空正2轉現金！")

st.markdown("---")
# ==========================================
# 區塊三：微笑曲線 (打勾清單簡化版)
# ==========================================
st.header("🔵 區塊三：微笑曲線打點表 (空頭反攻指標)")
cash_reserve = df.loc[df['資產類別'] == '撤退備戰金 (現金)', '市值'].values[0]
st.write(f"💡 目前可動用之【撤退備戰金】： **NT$ {cash_reserve:,.0f}**")

# 簡化版的文字格式
def get_smile_text(label, drop_rate, invest_ratio):
    target_price = sma_240 * (1 - drop_rate)
    budget = total_val * invest_ratio
    shares = int(budget / target_price) if target_price > 0 else 0
    return f"{label} ➔ 觸發價 **${target_price:.2f}** | 買 **{shares:,}** 股 (約 ${budget/10000:.0f}萬)"

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📉 左側下跌段")
    st.checkbox(get_smile_text("-8% (投5%)", 0.08, 0.05))
    st.checkbox(get_smile_text("-10% (投5%)", 0.10, 0.05))
    st.checkbox(get_smile_text("-15% (投5%)", 0.15, 0.05))
    st.checkbox(get_smile_text("-20% (投5%)", 0.20, 0.05))
    st.checkbox(get_smile_text("-25% (投5%)", 0.25, 0.05))
    st.checkbox(get_smile_text("-30% (投5%)", 0.30, 0.05))

with col_b:
    st.subheader("📈 右側上漲段")
    st.checkbox(get_smile_text("從 -8% 反彈 (投2%)", 0.08, 0.02))
    st.checkbox(get_smile_text("從 -10% 反彈 (投2%)", 0.10, 0.02))
    st.checkbox(get_smile_text("從 -15% 反彈 (投2%)", 0.15, 0.02))
    st.checkbox(get_smile_text("從 -20% 反彈 (投2%)", 0.20, 0.02))
    st.checkbox(get_smile_text("從 -25% 反彈 (投2%)", 0.25, 0.02))
    st.checkbox(get_smile_text("從 -30% 反彈 (投2%)", 0.30, 0.02))

st.error("🛑 提示：若跌破 -30% 深淵，請停止加碼，進入冬眠模式保護現金！")
