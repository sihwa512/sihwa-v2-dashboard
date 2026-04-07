import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

# 設定網頁標題與寬版顯示
st.set_page_config(page_title="Sihwa 資本 - V2 全自動投資儀表板", layout="wide")
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

st.header("📡 1. 系統連線：即時股價抓取 (Yahoo Finance)")
col1, col2, col3 = st.columns(3)

with st.spinner('機器人正在上網抓取最新股價，請稍候...'):
    price_00662 = get_stock_price("00662.TW")
    price_00670L = get_stock_price("00670L.TW")
    price_00865B = get_stock_price("00865B.TW")

col1.metric("原型底倉 (00662)", f"${price_00662:.2f}")
col2.metric("正2攻擊 (00670L)", f"${price_00670L:.2f}")
col3.metric("絕對保命金 (00865B)", f"${price_00865B:.2f}")

st.markdown("---")
st.header("📊 2. 資金配置與自動化圓餅圖")
st.write("您只需確認『持有股數』與『台幣現金』，系統會自動乘上最新股價幫您算好總市值！")

# 帶入 Sihwa 資本的實際佈局股數
shares_data = {
    "資產類別": ["原型底倉 (00662)", "正2攻擊 (00670L)", "絕對保命金 (00865B)", "撤退備戰金 (現金)"],
    "持有股數或金額": [113000, 5000000, 150000, 4308152],
    "今日系統抓取單價": [price_00662, price_00670L, price_00865B, 1.0]
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
st.info("💡 操作提示：若有加碼或賣出，只要直接修改上方表格內的『持有股數』然後按下 Enter，圓餅圖就會瞬間自動更新！")
