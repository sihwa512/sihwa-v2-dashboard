import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V2 終極全自動投資儀表板", layout="wide")
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
# 區塊一：資產配置 (整合試算表 表1)
# ==========================================
st.header("🟡 區塊一：資產配置與自動化圓餅圖")
st.write("您只需確認『持有股數』與『台幣現金』，系統會自動乘上最新股價幫您算好總市值！")

# 帶入 Sihwa 資本試算表的實際佈局股數
shares_data = {
    "資產類別": ["原型底倉 (00662A)", "原型加碼倉", "正2攻擊 (00670L)", "絕對保命金 (00865B)", "撤退備戰金 (現金)"],
    "持有股數或金額": [113000, 10000, 5000000, 150000, 4309152],
    "今日系統抓取單價": [price_00662, price_00662, price_00670L, price_00865B, 1.0]
}
df_shares = pd.DataFrame(shares_data)

# 讓網頁產生可編輯的表格
edited_df = st.data_editor(df_shares, use_container_width=True, hide_index=True)

# 系統自動相乘計算總市值
edited_df['總市值'] = edited_df['持有股數或金額'] * edited_df['今日系統抓取單價']

# 繪製會自動變形的圓餅圖
fig = px.pie(edited_df, values='總市值', names='資產類別', 
             title=f'目前總資產水位監控 (總市值: {edited_df["總市值"].sum():,.0f} 元)',
             color_discrete_sequence=px.colors.sequential.Teal)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
# ==========================================
# 區塊二：雙核雷達 (整合試算表 表2)
# ==========================================
st.header("🔴 區塊二：雙核雷達警報器 (多空防禦指標)")
st.write("系統會根據您輸入的年線，自動計算 00662A 偏離率並亮起對應燈號。")

col1, col2 = st.columns(2)
with col1:
    # 預設帶入試算表中的 93.49
    sma_240 = st.number_input("請輸入 00662A 目前的 240日均線(年線) 數值：", value=93.49, step=0.1)
    
    # 自動計算偏離率
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
# 區塊三：微笑曲線 (整合試算表 表3)
# ==========================================
st.header("🔵 區塊三：熊市微笑曲線打點表 (空頭反攻指標)")
st.write("跌破年線後，依跌幅階梯分批買入原型底倉：")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("📉 左側下跌段")
    st.checkbox("-8% (投入 5%)")
    st.checkbox("-10% (投入 5%)")
    st.checkbox("-15% (投入 5%)")
    st.checkbox("-20% (投入 5%)")
    st.checkbox("-25% (投入 5%)")
    st.checkbox("-30% (投入 5%)")

with col_b:
    st.subheader("📈 右側上漲段")
    st.checkbox("從 -8% 反彈 (投入 2%)")
    st.checkbox("從 -10% 反彈 (投入 2%)")
    st.checkbox("從 -15% 反彈 (投入 2%)")
    st.checkbox("從 -20% 反彈 (投入 2%)")
    st.checkbox("從 -25% 反彈 (投入 2%)")
    st.checkbox("從 -30% 反彈 (投入 2%)")

st.error("🛑 跌破 -30% 深淵：停止加碼，進入冬眠模式保護現金！")
