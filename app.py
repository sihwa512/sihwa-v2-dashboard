import streamlit as st
import yfinance as yf
import json
import os

# 設定網頁標題、寬版顯示與極簡 CSS
st.set_page_config(page_title="Sihwa 資本 - V10 極簡操盤版", layout="wide")
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("Sihwa 資本 | 雷恩 40-40-20 極簡操盤面板 🚀")

# ==========================================
# 資料抓取與存檔邏輯
# ==========================================
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
            return float(hist['Close'].iloc[-1]), 0.0, 0.0
    except:
        return 100.0, 0.0, 0.0

@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        return float(yf.Ticker("USDTWD=X").history(period="1d")['Close'].iloc[-1])
    except:
        return 32.5

DATA_FILE = "sihwa_settings.json"
def load_settings():
    default_settings = {
        "q_662b": 113000, "q_865b": 150000, "q_cash": 4309152, "q_662a": 0, "q_670l": 0,
        "sma_662": 93.49, "sma_qqq": 430.0
    }
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                for k, v in default_settings.items():
                    if k not in data: data[k] = v
                return data
        except:
            return default_settings
    return default_settings

if 'sys_set' not in st.session_state:
    st.session_state.sys_set = load_settings()

# ==========================================
# ⚙️ 隱藏式參數設定區 (點擊展開)
# ==========================================
with st.expander("⚙️ 點此展開設定：修改持有股數、現金與年線基準", expanded=False):
    st.markdown("在此修改您的真實持倉，修改完畢後點擊儲存，主畫面將自動以極簡模式呈現最新數據。")
    c1, c2, c3 = st.columns(3)
    
    q_662b = c1.number_input("🟦 原型底倉 (00662A) 股數", value=st.session_state.sys_set["q_662b"], step=1000)
    q_670l = c1.number_input("🟥 正2攻擊 (00670L) 股數", value=st.session_state.sys_set["q_670l"], step=1000)
    
    q_865b = c2.number_input("🟩 絕對保命金 (00865B) 股數", value=st.session_state.sys_set["q_865b"], step=1000)
    q_662a = c2.number_input("🟪 原型加碼倉 股數", value=st.session_state.sys_set["q_662a"], step=1000)
    
    q_cash = c3.number_input("⬜ 撤退備戰金 (現金) 金額", value=st.session_state.sys_set["q_cash"], step=10000)
    st.markdown("---")
    
    c4, c5, c6 = st.columns(3)
    sma_662 = c4.number_input("🇹🇼 00662A 240日年線", value=st.session_state.sys_set["sma_662"], step=0.1)
    sma_qqq = c5.number_input("🇺🇸 QQQ 240日年線", value=st.session_state.sys_set["sma_qqq"], step=0.5)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if c6.button("💾 儲存並更新儀表板", use_container_width=True):
        new_set = {
            "q_662b": q_662b, "q_865b": q_865b, "q_cash": q_cash, "q_662a": q_662a, "q_670l": q_670l,
            "sma_662": sma_662, "sma_qqq": sma_qqq
        }
        with open(DATA_FILE, "w") as f:
            json.dump(new_set, f)
        st.session_state.sys_set = new_set
        st.rerun()

# 同步變數
q_662b = st.session_state.sys_set["q_662b"]
q_865b = st.session_state.sys_set["q_865b"]
q_cash = st.session_state.sys_set["q_cash"]
q_662a = st.session_state.sys_set["q_662a"]
q_670l = st.session_state.sys_set["q_670l"]
sma_662 = st.session_state.sys_set["sma_662"]
sma_qqq = st.session_state.sys_set["sma_qqq"]

# ==========================================
# 🌐 即時市場報價
# ==========================================
st.header("🌐 即時市場報價")
with st.spinner('數據同步中...'):
    p_662, c_662, cp_662 = get_stock_data("00662.TW")
    p_670L, c_670L, cp_670L = get_stock_data("00670L.TW")
    p_865B, c_865B, cp_865B = get_stock_data("00865B.TW")
    p_qqq, c_qqq, cp_qqq = get_stock_data("QQQ")
    usd_twd = get_exchange_rate()

col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
col_p1.metric("00662A (原型)", f"${p_662:.2f}", f"{c_662:+.2f} ({cp_662:+.2f}%)")
col_p2.metric("00670L (正2)", f"${p_670L:.2f}", f"{c_670L:+.2f} ({cp_670L:+.2f}%)")
col_p3.metric("00865B (保命)", f"${p_865B:.2f}", f"{c_865B:+.2f} ({cp_865B:+.2f}%)")
col_p4.metric("QQQ (納指)", f"${p_qqq:.2f}", f"{c_qqq:+.2f} ({cp_qqq:+.2f}%)")
col_p5.metric("USD/TWD", f"${usd_twd:.2f}")

# ==========================================
# 💰 帳戶總覽與極簡比例
# ==========================================
st.header("💰 帳戶總覽與 Beta 控管")

# 核心計算
val_662b = q_662b * p_662
val_662a = q_662a * p_662
val_670l = q_670l * p_670L
val_865b = q_865b * p_865B
val_cash = q_cash * 1.0

total_val = val_662b + val_662a + val_670l + val_865b + val_cash
pct_662b = (val_662b / total_val) * 100 if total_val else 0
pct_662a = (val_662a / total_val) * 100 if total_val else 0
pct_670l = (val_670l / total_val) * 100 if total_val else 0
pct_865b = (val_865b / total_val) * 100 if total_val else 0
pct_cash = (val_cash / total_val) * 100 if total_val else 0

today_pnl = (q_662b * c_662) + (q_662a * c_662) + (q_670l * c_670L) + (q_865b * c_865B)
current_beta = (val_662b*1.0 + val_662a*1.0 + val_670l*2.0) / total_val if total_val else 0

# 四大核心數據
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("總資產淨值", f"NT$ {total_val:,.0f}")
col_m2.metric("今日總損益", f"NT$ {today_pnl:,.0f}", f"{(today_pnl/total_val)*100:+.2f}%" if total_val > 0 else "0.00%")
col_m3.metric("🎯 目標 Beta", "1.20")
col_m4.metric("📈 實質 Beta", f"{current_beta:.2f}", f"{current_beta - 1.20:+.2f}", delta_color="inverse")

# 極簡化佔比呈現 (取代原本的表格)
st.markdown("<br>", unsafe_allow_html=True)
ca1, ca2, ca3, ca4, ca5 = st.columns(5)
ca1.metric(f"🟦 原型底倉 ({pct_662b:.1f}%)", f"${val_662b:,.0f}")
ca2.metric(f"🟩 保命金 ({pct_865b:.1f}%)", f"${val_865b:,.0f}")
ca3.metric(f"⬜ 備戰金 ({pct_cash:.1f}%)", f"${val_cash:,.0f}")
ca4.metric(f"🟪 加碼倉 ({pct_662a:.1f}%)", f"${val_662a:,.0f}")
ca5.metric(f"🟥 正2攻擊 ({pct_670l:.1f}%)", f"${val_670l:,.0f}")

# ==========================================
# 🔴 雙核防禦雷達 (狀態燈號化)
# ==========================================
st.header("🔴 雙核防禦雷達")
bias_662 = ((p_662 - sma_662) / sma_662) * 100
bias_qqq = ((p_qqq - sma_qqq) / sma_qqq) * 100

cr1, cr2 = st.columns(2)
with cr1:
    if bias_662 >= 0:
        st.success(f"🇹🇼 **00662A 偏離率: {bias_662:.2f}%** (站穩年線) ➔ 🟢 安全續抱")
    elif bias_662 >= -3:
        st.warning(f"🇹🇼 **00662A 偏離率: {bias_662:.2f}%** (跌破年線) ➔ 🟡 警戒防守，觀察三日")
    else:
        st.error(f"🇹🇼 **00662A 偏離率: {bias_662:.2f}%** (深跌破破) ➔ 🔴 危險撤退，清空正2！")

with cr2:
    if bias_qqq >= 0:
        st.success(f"🇺🇸 **QQQ 偏離率: {bias_qqq:.2f}%** (站穩年線) ➔ 🟢 美股大盤健康")
    else:
        st.error(f"🇺🇸 **QQQ 偏離率: {bias_qqq:.2f}%** (跌破年線) ➔ 🔴 大盤轉弱，防禦準備！")

# ==========================================
# 🔵 微笑曲線計畫 (極簡版)
# ==========================================
st.header("🔵 微笑曲線分批買入計畫")
st.markdown(f"**💡 目前備戰現金餘額： NT$ {val_cash:,.0f}**")

def get_smile_text(label, drop_rate, invest_ratio):
    target_price = sma_662 * (1 - drop_rate)
    budget = total_val * invest_ratio
    shares = int(budget / target_price) if target_price > 0 else 0
    return f"{label} ➔ 觸發價 **${target_price:.2f}** | 買 **{shares:,}** 股 (約 ${budget/10000:.0f}萬)"

cc1, cc2 = st.columns(2)
with cc1:
    st.checkbox(get_smile_text("📉 -8% (投5%)", 0.08, 0.05))
    st.checkbox(get_smile_text("📉 -10% (投5%)", 0.10, 0.05))
    st.checkbox(get_smile_text("📉 -15% (投5%)", 0.15, 0.05))
    st.checkbox(get_smile_text("📉 -20% (投5%)", 0.20, 0.05))
    st.checkbox(get_smile_text("📉 -25% (投5%)", 0.25, 0.05))
    st.checkbox(get_smile_text("📉 -30% (投5%)", 0.30, 0.05))

with cc2:
    st.checkbox(get_smile_text("📈 從 -8% 反彈 (投2%)", 0.08, 0.02))
    st.checkbox(get_smile_text("📈 從 -10% 反彈 (投2%)", 0.10, 0.02))
    st.checkbox(get_smile_text("📈 從 -15% 反彈 (投2%)", 0.15, 0.02))
    st.checkbox(get_smile_text("📈 從 -20% 反彈 (投2%)", 0.20, 0.02))
    st.checkbox(get_smile_text("📈 從 -25% 反彈 (投2%)", 0.25, 0.02))
    st.checkbox(get_smile_text("📈 從 -30% 反彈 (投2%)", 0.30, 0.02))
