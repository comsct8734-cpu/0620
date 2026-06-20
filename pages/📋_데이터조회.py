import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(
    page_title="데이터 조회",
    page_icon="📋",
    layout="wide"
)

st.title("📋 데이터 조회")
st.markdown("#### 전체 지진 데이터 조회 및 다운로드")

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
    
    st.success(f"✅ {len(earthquakes_df):,}개의 지진 데이터 조회")
    
    # 데이터 표시
    display_df = earthquakes_df.copy()
    display_df["time"] = display_df["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
    display_df = display_df.rename(columns={
        "latitude": "위도",
        "longitude": "경도",
        "depth": "깊이(km)",
        "magnitude": "규모",
        "place": "위치",
        "time": "시간"
    })
    
    # 정렬 옵션
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox(
            "정렬 기준",
            ["시간", "규모", "위도", "경도", "깊이(km)"]
        )
    with col2:
        ascending = st.checkbox("오름차순", value=False)
    
    # 정렬
    display_df = display_df.sort_values(by=sort_by, ascending=ascending)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # CSV 다운로드
    csv = display_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 CSV로 다운로드",
        data=csv,
        file_name=f"earthquakes_{start_year}_{end_year}.csv",
        mime="text/csv"
    )
