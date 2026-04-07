import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V5 專業操盤手儀表板", layout="wide")
st.title("Sihwa 資本 | 雷恩 40-40-20 專業儀表板 🚀")
st.markdown("---")

# 1. 設定自動抓取「最新股價」與「昨日收盤價(算損益)」的工具
@st.cache_data(ttl=900)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 抓取近 5 天資料以防遇到假日
        hist = stock.history(period="5d")
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            current = hist['Close'].iloc[-1]
        else:
            prev_close = hist['Close'].iloc[-1]
            current = hist['Close'].iloc[-1]
        change = current - prev_close
        return float(current), float(change)
    except:
        return 100.0, 0.0

# 2. 抓取匯率
@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        rate = yf.Ticker("USDTWD=X").history(period="1d")['Close'].iloc[-1]
        return float(rate)
    except:
        return 32.0

# 3. 抓取近一年歷史資料 (用於畫淨值曲線)
@st.cache_data(ttl=86400)
def get_historical_prices():
    try:
        t1 = yf.Ticker("00662.TW").history(period="1y")['Close']
        t2 = yf.Ticker("00670L.TW").history(period="1y")['Close']
        t3 = yf.Ticker("00865B.TW").history(period="1y")['Close']
        df = pd.DataFrame({"00662A": t1, "00670L": t2, "00865B": t3}).fillna(method='ffill').dropna()
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 頂部即時看盤區 (加入匯率與漲跌)
# ==========================================
st.header("📡 系統連線：即時報價與匯率")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)

with st.spinner('機器人正在上網抓取最新報價，請稍候...'):
    price_00662, change_00662 = get_stock_data("00662.TW")
    price_00670L, change_00670L = get_stock_data("00670L.TW")
    price_00865B, change_00865B = get_stock_data("00865B.TW")
    usd_twd = get_exchange_rate()

col_p1.metric("原型底倉 (00662A)", f"${price_00662:.2f}", f"{change_00662:.2f}")
col_p2.metric("正2攻擊 (00670L)", f"${price_00670L:.2f}", f"{change_00670L:.2f}")
col_p3.metric("絕對保命金 (00865B)", f"${price_00865B:.2f}", f"{change_00865B:.2f}")
col_p4.metric("USD/TWD 美元匯率", f"${usd_twd:.2f}")

st.markdown("---")
# ==========================================
# 區塊一：資產配置與歷史淨值曲線
# ==========================================
st.header("🟡 區塊一：部位管理與淨值曲線")

if 'shares_data' not in st.session_state:
    st.session_state.shares_data = pd.DataFrame({
        "資產類別": ["原型底倉 (00662A)", "原型加碼倉", "正2攻擊 (00670L)", "絕對保命金 (00865B)", "撤退備戰金 (現金)"],
        "持有股數或金額": [113000, 10000, 5000000, 150000, 4309152],
        "今日單價": [0.0, 0.0, 0.0, 0.0, 1.0],
        "目標佔比": ["40%", "0%", "40%", "20%", "0%"]
    })

# 寫入最新單價並計算總市值
st.session_state.shares_data['今日單價'] = [price_00662, price_00662, price_00670L, price_00865B, 1.0]
st.session_state.shares_data['市值'] = st.session_state.shares_data['持有股數或金額'] * st.session_state.shares_data['今日單價']
total_value = st.session_state.shares_data['市值'].sum()
st.session_state.shares_data['佔比(自動)'] = (st.session_state.shares_data['市值'] / total_value).apply(lambda x: f"{x*100:.2f}%")

# 計算「今日損益」
qty_00662_total = st.session_state.shares_data.loc[0, '持有股數或金額'] + st.session_state.shares_data.loc[1, '持有股數或金額']
qty_00670L = st.session_state.shares_data.loc[2, '持有股數或金額']
qty_00865B = st.session_state.shares_data.loc[3, '持有股數或金額']
cash_val = st.session_state.shares_data.loc[4, '持有股數或金額']

today_pnl = (qty_00662_total * change_00662) + (qty_00670L * change_00670L) + (qty_00865B * change_00865B)

# 顯示總淨值與今日損益 (放大顯示)
st.metric(label="💰 目前總資產淨值", value=f"NT$ {total_value:,.0f}", delta=f"今日損益: {today_pnl:,.0f} 元")

edited_df = st.data_editor(
    st.session_state.shares_data,
    column_config={
        "今日單價": st.column_config.NumberColumn(format="$%.2f"),
        "市值": st.column_config.NumberColumn(format="$%d"),
    },
    disabled=["資產類別", "今日單價", "市值", "目標佔比", "佔比(自動)"],
    hide_index=True,
    use_container_width=True
)

if not edited_df['持有股數或金額'].equals(st.session_state.shares_data['持有股數或金額']):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.rerun()

# 繪製歷史淨值曲線 (取代圓餅圖)
df_hist = get_historical_prices()
if not df_hist.empty:
    # 以當前持股回測過去一年的淨值
    df_hist['總淨值'] = (df_hist['00662A'] * qty_00662_total) + \
                      (df_hist['00670L'] * qty_00670L) + \
                      (df_hist['00865B'] * qty_00865B) + cash_val
    
    fig_line = px.line(df_hist, y='總淨值', title='📈 近一年歷史淨值走勢 (模擬當前持股部位)')
    fig_line.update_layout(yaxis_title="總市值 (NT$)", xaxis_title="日期", hovermode="x unified")
    fig_line.update_traces(line_color='#17A2B8', line_width=2)
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("歷史資料抓取中，請稍後重整網頁...")

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達 
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器 (多空防禦指標)")
col1, col2 = st.columns(2)
with col1:
    sma_240 = st.number_input("請輸入 00662A 目前的 240日均線(年線) 數值：", value=93.49, step=0.1)
    bias = ((price_00662 - sma_240) / sma_240) * 100
    st.metric(label="00662A 距離年線偏離率", value=f"{bias:.2f}%", delta="在年線之上" if bias > 0 else "跌破年線")

with col2:
    if bias >= 0:
        st.success("🟩 系統判定：安全 (大於0%)，持股續抱，維持 40-40-20")
    elif bias >= -3:
        st.warning("🟨 系統判定：警戒 (跌破年線但未滿-3%)，觀察是否連續三日站不回")
    else:
        st.error("🟥 系統判定：危險撤退 (跌破-3%)，無情清空正2轉備戰現金！")

st.markdown("---")
# ==========================================
# 區塊三：微笑曲線 (年線連動精算版)
# ==========================================
st.header("🔵 區塊三：熊市微笑曲線打點表 (空頭反攻指標)")
st.markdown(f"💡 **目前可動用之【撤退備戰金 (現金)】餘額： NT$ {cash_val:,.0f}**")

def get_smile_text(label, drop_rate, invest_ratio):
    target_price = sma_240 * (1 - drop_rate)
    amount = total_value * invest_ratio
    shares = int(amount / target_price) if target_price > 0 else 0
    return f"{label} ➔ 觸發價: **${target_price:.2f}** | 動用現金: ${amount:,.0f} | 預計買入: **{shares:,}** 股"

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📉 左側下跌段")
    st.checkbox(get_smile_text("-8% (投入 5%)", 0.08, 0.05))
    st.checkbox(get_smile_text("-10% (投入 5%)", 0.10, 0.05))
    st.checkbox(get_smile_text("-15% (投入 5%)", 0.15, 0.05))
    st.checkbox(get_smile_text("-20% (投入 5%)", 0.20, 0.05))
    st.checkbox(get_smile_text("-25% (投入 5%)", 0.25, 0.05))
    st.checkbox(get_smile_text("-30% (投入 5%)", 0.30, 0.05))

with col_b:
    st.subheader("📈 右側上漲段")
    st.checkbox(get_smile_text("從 -8% 反彈 (投入 2%)", 0.08, 0.02))
    st.checkbox(get_smile_text("從 -10% 反彈 (投入 2%)", 0.10, 0.02))
    st.checkbox(get_smile_text("從 -15% 反彈 (投入 2%)", 0.15, 0.02))
    st.checkbox(get_smile_text("從 -20% 反彈 (投入 2%)", 0.20, 0.02))
    st.checkbox(get_smile_text("從 -25% 反彈 (投入 2%)", 0.25, 0.02))
    st.checkbox(get_smile_text("從 -30% 反彈 (投入 2%)", 0.30, 0.02))

st.error("🛑 跌破 -30% 深淵：停止加碼，進入冬眠模式保護現金！")
