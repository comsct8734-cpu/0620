import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px

st.set_page_config(
    page_title="통계 분석",
    page_icon="📊",
    layout="wide"
)

st.title("📊 통계 분석")
st.markdown("#### 지진 데이터 분석 및 시각화")

# API에서 지진 데이터 가져오기
@st.cache_data(ttl=3600)
def fetch_earthquake_data(start_year, end_year):
    """USGS API에서 지진 데이터 가져오기"""
    try:
        start_date = f"{start_year}-01-01"
        end_date = f"{end_year}-12-31"
        
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/query"
        params = {
            "starttime": start_date,
            "endtime": end_date,
            "format": "geojson",
            "minmagnitude": 2.5
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        features = data.get("features", [])
        
        earthquakes = []
        for feature in features:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            
            earthquakes.append({
                "longitude": coords[0],
                "latitude": coords[1],
                "depth": coords[2],
                "magnitude": props.get("mag"),
                "place": props.get("place"),
                "time": datetime.fromtimestamp(props.get("time", 0) / 1000)
            })
        
        return pd.DataFrame(earthquakes)
    
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        return pd.DataFrame()

# 사이드바
with st.sidebar:
    st.header("⚙️ 필터 설정")
    
    current_year = datetime.now().year
    year_range = st.slider(
        "연도 범위",
        min_value=2010,
        max_value=current_year,
        value=(current_year - 1, current_year),
        step=1
    )
    
    start_year, end_year = year_range
    
    min_magnitude = st.slider(
        "최소 규모",
        min_value=2.5,
        max_value=9.0,
        value=2.5,
        step=0.1
    )

# 데이터 로드
with st.spinner("📡 데이터 로드 중..."):
    earthquakes_df = fetch_earthquake_data(start_year, end_year)

if earthquakes_df.empty:
    st.warning("⚠️ 해당 기간에 데이터가 없습니다.")
else:
    # 규모 필터
    earthquakes_df = earthquakes_df[earthquakes_df["magnitude"] >= min_magnitude]
    
    st.success(f"✅ {len(earthquakes_df):,}개의 지진 데이터 분석")
    
    # 차트
    col1, col2 = st.columns(2)
    
    with col1:
        fig_mag = px.histogram(
            earthquakes_df,
            x="magnitude",
            nbins=20,
            title="지진 규모 분포",
            color_discrete_sequence=["#FF6B6B"]
        )
        st.plotly_chart(fig_mag, use_container_width=True)
    
    with col2:
        fig_depth = px.histogram(
            earthquakes_df,
            x="depth",
            nbins=20,
            title="지진 깊이 분포",
            color_discrete_sequence=["#4ECDC4"]
        )
        st.plotly_chart(fig_depth, use_container_width=True)
    
    # 시간별 추세
    earthquakes_df["date"] = earthquakes_df["time"].dt.date
    daily = earthquakes_df.groupby("date").size().reset_index(name="count")
    
    fig_trend = px.line(
        daily,
        x="date",
        y="count",
        title="시간에 따른 지진 발생 추세",
        markers=True
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # 상위 지진
    st.subheader("🔴 가장 큰 규모의 지진 TOP 10")
    top_earthquakes = earthquakes_df.nlargest(10, "magnitude")[
        ["time", "magnitude", "place", "depth"]
    ].copy()
    top_earthquakes["time"] = top_earthquakes["time"].dt.strftime("%Y-%m-%d %H:%M")
    top_earthquakes = top_earthquakes.rename(columns={
        "time": "시간",
        "magnitude": "규모",
        "place": "위치",
        "depth": "깊이(km)"
    })
    st.dataframe(top_earthquakes, use_container_width=True, hide_index=True)
