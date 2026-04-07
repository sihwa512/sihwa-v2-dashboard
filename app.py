import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V3 終極全自動投資儀表板", layout="wide")
st.title("Sihwa 資本 | 雷恩 40-40-20 全自動儀表板 🚀")
st.markdown("---")

# 設定自動抓取最新股價的工具
@st.cache_data(ttl=900)
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close'].iloc[-1]
        return float(price)
    except:
        return 100.0 # 預設防呆數值

st.header("📡 系統連線：即時股價抓取 (Yahoo Finance)")
col_p1, col_p2, col_p3 = st.columns(3)

with st.spinner('機器人正在上網抓取最新股價，請稍候...'):
    price_00662 = get_stock_price("00662.TW")
    price_00670L = get_stock_price("00670L.TW")
    price_00865B = get_stock_price("00865B.TW")

col_p1.metric("原型底倉 (00662A)", f"${price_00662:.2f}")
col_p2.metric("正2攻擊 (00670L)", f"${price_00670L:.2f}")
col_p3.metric("絕對保命金 (00865B)", f"${price_00865B:.2f}")

st.markdown("---")
# ==========================================
# 區塊一：資產配置
# ==========================================
st.header("🟡 區塊一：資產配置與自動化圓餅圖")

# 1. 建立 Session State 來儲存並連動計算結果
if 'shares_data' not in st.session_state:
    st.session_state.shares_data = pd.DataFrame({
        "資產類別": ["原型底倉 (00662A)", "原型加碼倉", "正2攻擊 (00670L)", "絕對保命金 (00865B)", "撤退備戰金 (現金)"],
        "持有股數或金額": [113000, 10000, 5000000, 150000, 4309152],
        "今日單價": [0.0, 0.0, 0.0, 0.0, 1.0],
        "目標佔比": ["40%", "0%", "40%", "20%", "0%"]
    })

# 2. 寫入最新單價
st.session_state.shares_data['今日單價'] = [price_00662, price_00662, price_00670L, price_00865B, 1.0]

# 3. 計算市值與佔比
st.session_state.shares_data['市值'] = st.session_state.shares_data['持有股數或金額'] * st.session_state.shares_data['今日單價']
total_value = st.session_state.shares_data['市值'].sum()
st.session_state.shares_data['佔比(自動)'] = (st.session_state.shares_data['市值'] / total_value).apply(lambda x: f"{x*100:.2f}%")

# [新增] 總市值放置於開頭
st.markdown(f"### 💰 目前總資產市值： **NT$ {total_value:,.0f}**")
st.write("您只需修改『持有股數或金額』，按下 Enter 後系統會自動更新所有佔比與下方圖表！")

# 4. 顯示互動表格 (支援金錢格式顯示)
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

# 5. 偵測股數變動並重新計算整個網頁
if not edited_df['持有股數或金額'].equals(st.session_state.shares_data['持有股數或金額']):
    st.session_state.shares_data['持有股數或金額'] = edited_df['持有股數或金額']
    st.rerun()

# 繪製會自動變形的圓餅圖
fig = px.pie(st.session_state.shares_data, values='市值', names='資產類別', 
             color_discrete_sequence=px.colors.sequential.Teal)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達 
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器 (多空防禦指標)")
st.write("系統會根據您輸入的年線，自動計算 00662A 偏離率並亮起對應燈號。")

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
# 區塊三：微笑曲線 (加入自動精算股數)
# ==========================================
st.header("🔵 區塊三：熊市微笑曲線打點表 (空頭反攻指標)")
st.write("跌破年線後分批買入原型底倉。系統已根據 **即時總市值** 與 **即時股價** 幫您算好確切的購買數量：")

# 建立動態計算函數，直接將金額與股數秀出來
def get_smile_text(label, invest_ratio):
    amount = total_value * invest_ratio
    shares = int(amount / price_00662) if price_00662 > 0 else 0
    return f"{label} ➔ 金額: ${amount:,.0f} | 約買 {shares:,} 股 (股價 ${price_00662:.2f})"

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📉 左側下跌段")
    st.checkbox(get_smile_text("-8% (投入 5%)", 0.05))
    st.checkbox(get_smile_text("-10% (投入 5%)", 0.05))
    st.checkbox(get_smile_text("-15% (投入 5%)", 0.05))
    st.checkbox(get_smile_text("-20% (投入 5%)", 0.05))
    st.checkbox(get_smile_text("-25% (投入 5%)", 0.05))
    st.checkbox(get_smile_text("-30% (投入 5%)", 0.05))

with col_b:
    st.subheader("📈 右側上漲段")
    st.checkbox(get_smile_text("從 -8% 反彈 (投入 2%)", 0.02))
    st.checkbox(get_smile_text("從 -10% 反彈 (投入 2%)", 0.02))
    st.checkbox(get_smile_text("從 -15% 反彈 (投入 2%)", 0.02))
    st.checkbox(get_smile_text("從 -20% 反彈 (投入 2%)", 0.02))
    st.checkbox(get_smile_text("從 -25% 反彈 (投入 2%)", 0.02))
    st.checkbox(get_smile_text("從 -30% 反彈 (投入 2%)", 0.02))

st.error("🛑 跌破 -30% 深淵：停止加碼，進入冬眠模式保護現金！")
