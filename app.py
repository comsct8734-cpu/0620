import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="🌍 Global Earthquake Visualization",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Global Earthquake Visualization")
st.markdown("#### USGS Earthquake Hazards Program")

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
    st.header("⚙️ 설정")
    
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
    
    st.success(f"✅ {len(earthquakes_df):,}개의 지진 데이터 로드")
    
    # 메트릭
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 지진 수", f"{len(earthquakes_df):,}")
    col2.metric("평균 규모", f"{earthquakes_df['magnitude'].mean():.1f}")
    col3.metric("최대 규모", f"{earthquakes_df['magnitude'].max():.1f}")
    col4.metric("최대 깊이(km)", f"{earthquakes_df['depth'].max():.0f}")
    
    # 탭
    tab1, tab2, tab3 = st.tabs(["🗺️ 지도", "📊 차트", "📋 데이터"])
    
    with tab1:
        st.subheader("지진 분포 지도")
        
        m = folium.Map(
            location=[20, 0],
            zoom_start=2,
            tiles="OpenStreetMap"
        )
        
        # 최대 500개까지만 표시 (성능)
        for idx, row in earthquakes_df.head(500).iterrows():
            mag = row["magnitude"]
            
            if mag < 4.5:
                color, radius = "green", 4
            elif mag < 6.0:
                color, radius = "orange", 6
            else:
                color, radius = "red", 8
            
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                popup=f"{mag:.1f} - {row['place']}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=1
            ).add_to(m)
        
        st_folium(m, width=1400, height=600)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_mag = px.histogram(
                earthquakes_df,
                x="magnitude",
                nbins=20,
                title="규모 분포",
                color_discrete_sequence=["#FF6B6B"]
            )
            st.plotly_chart(fig_mag, use_container_width=True)
        
        with col2:
            fig_depth = px.histogram(
                earthquakes_df,
                x="depth",
                nbins=20,
                title="깊이 분포",
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
            title="시간에 따른 지진 발생",
            markers=True
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with tab3:
        st.subheader("전체 데이터")
        
        display_df = earthquakes_df.copy()
        display_df["time"] = display_df["time"].dt.strftime("%Y-%m-%d %H:%M")
        display_df = display_df[["time", "magnitude", "place", "depth", "latitude", "longitude"]]
        display_df = display_df.rename(columns={
            "time": "시간",
            "magnitude": "규모",
            "place": "위치",
            "depth": "깊이(km)",
            "latitude": "위도",
            "longitude": "경도"
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 다운로드
        csv = display_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 CSV 다운로드",
            csv,
            f"earthquakes_{start_year}_{end_year}.csv",
            "text/csv"
        )

st.markdown("---")
st.markdown("""
<div style='text-align: center; font-size: 12px; color: gray;'>
📊 데이터 출처: <a href='https://www.usgs.gov/' target='_blank'>USGS</a> | 
🔄 데이터는 1시간마다 자동 갱신
</div>
""", unsafe_allow_html=True)
