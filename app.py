import streamlit as st
import pandas as pd
import yfinance as yf
import os

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V9 視覺美化版", layout="wide")
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
    p_qqq, c_qqq, cp_qqq = get_stock_data("QQQ")
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
            "資產類別": ["原型底倉 (00662A)", "絕對保命金 (00865B)", "撤退備戰金 (現金)", "原型加碼倉", "正2攻擊 (00670L)"],
            "持有股數或金額": [113000, 150000, 4309152, 0, 0]
        })

if 'shares_data' not in st.session_state:
    st.session_state.shares_data = load_data()

df = st.session_state.shares_data.copy()

# 強制排序與屬性映射 (防止舊存檔亂序)
cat_order = ["原型底倉 (00662A)", "絕對保命金 (00865B)", "撤退備戰金 (現金)", "原型加碼倉", "正2攻擊 (00670L)"]
df['資產類別'] = pd.Categorical(df['資產類別'], categories=cat_order, ordered=True)
df = df.sort_values('資產類別').reset_index(drop=True)

price_map = {"原型底倉 (00662A)": p_662, "絕對保命金 (00865B)": p_865B, "撤退備戰金 (現金)": 1.0, "原型加碼倉": p_662, "正2攻擊 (00670L)": p_670L}
beta_map = {"原型底倉 (00662A)": 1.0, "絕對保命金 (00865B)": 0.0, "撤退備戰金 (現金)": 0.0, "原型加碼倉": 1.0, "正2攻擊 (00670L)": 2.0}
target_map = {"原型底倉 (00662A)": "40%", "絕對保命金 (00865B)": "20%", "撤退備戰金 (現金)": "0%", "原型加碼倉": "0%", "正2攻擊 (00670L)": "40%"}

df['今日單價'] = df['資產類別'].map(price_map)
df['個股Beta'] = df['資產類別'].map(beta_map)
df['目標佔比'] = df['資產類別'].map(target_map)

# 計算市值與佔比
df['市值'] = df['持有股數或金額'] * df['今日單價']
total_val = df['市值'].sum()
df['佔比'] = (df['市值'] / total_val) if total_val > 0 else 0

# 安全計算今日損益
q_662_b = df.loc[df['資產類別'] == '原型底倉 (00662A)', '持有股數或金額'].values[0]
q_662_a = df.loc[df['資產類別'] == '原型加碼倉', '持有股數或金額'].values[0]
q_670L = df.loc[df['資產類別'] == '正2攻擊 (00670L)', '持有股數或金額'].values[0]
q_865B = df.loc[df['資產類別'] == '絕對保命金 (00865B)', '持有股數或金額'].values[0]
today_pnl = (q_662_b * c_662) + (q_662_a * c_662) + (q_670L * c_670L) + (q_865B * c_865B)

# 計算 Beta
current_beta = (df['佔比'] * df['個股Beta']).sum()
target_beta = 1.20

# 顯示數據牆
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("💰 目前總資產淨值", f"NT$ {total_val:,.0f}")
col_m2.metric("📊 今日總損益", f"NT$ {today_pnl:,.0f}", f"{(today_pnl/total_val)*100:+.2f}%" if total_val > 0 else "0.00%")
col_m3.metric("🎯 目標總 Beta", f"{target_beta:.2f}")
col_m4.metric("📈 目前實質 Beta", f"{current_beta:.2f}", f"{current_beta - target_beta:+.2f}", delta_color="inverse")

# 顯示表格 (加入目標佔比)
df['佔比(自動)'] = df['佔比'].apply(lambda x: f"{x*100:.2f}%")
edited_df = st.data_editor(
    df[["資產類別", "持有股數或金額", "今日單價", "市值", "目標佔比", "佔比(自動)", "個股Beta"]],
    column_config={"市值": st.column_config.NumberColumn(format="$%d")},
    disabled=["資產類別", "今日單價", "市值", "目標佔比", "佔比(自動)", "個股Beta"],
    hide_index=True, use_container_width=True
)

# 儲存按鈕
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("💾 儲存最新股數", use_container_width=True):
        save_df = edited_df[["資產類別", "持有股數或金額"]]
        save_df.to_csv(DATA_FILE, index=False)
        st.session_state.shares_data = save_df
        st.success("✅ 儲存成功！")
        st.rerun()

if not edited_df['持有股數或金額'].equals(st.session_state.shares_data['持有股數或金額']):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.rerun()

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達 (優化視覺版)
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器 (台美雙指標)")
st.markdown("請設定您的防守底線，系統將為您自動監控偏離率：")

# 使用美觀的卡片式排版取代生硬表格
col_r1, col_r2 = st.columns(2)

with col_r1:
    st.info("🇹🇼 **台股指標：00662A 監控**")
    sma_240 = st.number_input("設定 240日年線 (TWD)：", value=93.49, step=0.1)
    bias_662 = ((p_662 - sma_240) / sma_240) * 100
    st.metric(label="目前偏離率", value=f"{bias_662:.2f}%", delta="站穩年線" if bias_662 > 0 else "跌破年線", delta_color="normal" if bias_662 > 0 else "inverse")
    if bias_662 >= 0:
        st.success("🟢 狀態：安全續抱")
    elif bias_662 >= -3:
        st.warning("🟡 狀態：警戒防守，觀察三日")
    else:
        st.error("🔴 狀態：危險撤退，無情清空正2！")

with col_r2:
    st.info("🇺🇸 **美股指標：QQQ 監控**")
    qqq_sma_240 = st.number_input("設定 240日年線 (USD)：", value=430.0, step=0.5)
    bias_qqq = ((p_qqq - qqq_sma_240) / qqq_sma_240) * 100
    st.metric(label=f"目前偏離率 (現價 ${p_qqq:.2f})", value=f"{bias_qqq:.2f}%", delta="站穩年線" if bias_qqq > 0 else "跌破年線", delta_color="normal" if bias_qqq > 0 else "inverse")
    if bias_qqq >= 0:
        st.success("🟢 狀態：美股大盤健康")
    else:
        st.error("🔴 狀態：美股大盤轉弱，防禦準備！")

st.markdown("---")
# ==========================================
# 區塊三：微笑曲線 (打勾清單)
# ==========================================
st.header("🔵 區塊三：微笑曲線打點表")
cash_reserve = df.loc[df['資產類別'] == '撤退備戰金 (現金)', '市值'].values[0]
st.write(f"💡 目前可動用之【撤退備戰金】： **NT$ {cash_reserve:,.0f}**")

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
