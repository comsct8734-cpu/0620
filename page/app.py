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
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌍 Global Earthquake Visualization")
st.markdown("#### USGS Earthquake Hazards Program - Real-time Data")

# 캐싱을 사용하여 API 호출 최적화
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
            "minmagnitude": 2.5  # 규모 2.5 이상만 표시
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        features = data.get("features", [])
        
        # GeoJSON을 DataFrame으로 변환
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
                "time": datetime.fromtimestamp(props.get("time", 0) / 1000),
                "url": props.get("url")
            })
        
        return pd.DataFrame(earthquakes)
    
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        return pd.DataFrame()

# 사이드바 컨트롤
with st.sidebar:
    st.header("⚙️ 설정")
    
    # 연도 선택
    current_year = datetime.now().year
    year_range = st.slider(
        "연도 범위 선택",
        min_value=2010,
        max_value=current_year,
        value=(current_year - 1, current_year),
        step=1
    )
    
    start_year, end_year = year_range
    
    # 규모 필터
    min_magnitude = st.slider(
        "최소 지진 규모",
        min_value=2.5,
        max_value=9.0,
        value=2.5,
        step=0.1
    )
    
    st.markdown("---")
    st.markdown("**📊 범례**")
    st.markdown("🟢 규모 2.5-4.5")
    st.markdown("🟡 규모 4.5-6.0")
    st.markdown("🔴 규모 6.0 이상")

# 데이터 로드
st.markdown("### 📡 데이터 로드 중...")
earthquakes_df = fetch_earthquake_data(start_year, end_year)

if earthquakes_df.empty:
    st.warning("해당 기간에 지진 데이터가 없습니다.")
else:
    # 규모 필터 적용
    earthquakes_df = earthquakes_df[earthquakes_df["magnitude"] >= min_magnitude]
    
    st.success(f"✅ {len(earthquakes_df)}개의 지진 데이터 로드 완료!")
    
    # 통계 정보
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 지진 수", len(earthquakes_df))
    
    with col2:
        avg_mag = earthquakes_df["magnitude"].mean()
        st.metric("평균 규모", f"{avg_mag:.1f}")
    
    with col3:
        max_mag = earthquakes_df["magnitude"].max()
        st.metric("최대 규모", f"{max_mag:.1f}")
    
    with col4:
        max_depth = earthquakes_df["depth"].max()
        st.metric("최대 깊이 (km)", f"{max_depth:.0f}")
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["🗺️ 지도", "📈 통계", "📋 데이터"]
    )
    
    with tab1:
        st.subheader("지진 분포 지도")
        
        # 폴리움 지도 생성
        m = folium.Map(
            location=[20, 0],
            zoom_start=2,
            tiles="OpenStreetMap"
        )
        
        # 지진 데이터를 규모별로 색상 분류
        for idx, row in earthquakes_df.iterrows():
            magnitude = row["magnitude"]
            
            # 규모에 따른 색상 결정
            if magnitude < 4.5:
                color = "green"
                radius = 5
            elif magnitude < 6.0:
                color = "orange"
                radius = 8
            else:
                color = "red"
                radius = 12
            
            popup_text = f"""
            <b>규모:</b> {magnitude:.1f}<br>
            <b>위치:</b> {row['place']}<br>
            <b>깊이:</b> {row['depth']:.1f} km<br>
            <b>시간:</b> {row['time'].strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                popup=folium.Popup(popup_text, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=2
            ).add_to(m)
        
        st_folium(m, width=1400, height=600)
    
    with tab2:
        st.subheader("지진 데이터 분석")
        
        # 규모 분포
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist = px.histogram(
                earthquakes_df,
                x="magnitude",
                nbins=20,
                title="지진 규모 분포",
                labels={"magnitude": "지진 규모"},
                color_discrete_sequence=["#FF6B6B"]
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            fig_depth = px.histogram(
                earthquakes_df,
                x="depth",
                nbins=20,
                title="지진 깊이 분포",
                labels={"depth": "깊이 (km)"},
                color_discrete_sequence=["#4ECDC4"]
            )
            st.plotly_chart(fig_depth, use_container_width=True)
        
        # 시간에 따른 지진 발생 추세
        earthquakes_df["date"] = earthquakes_df["time"].dt.date
        daily_count = earthquakes_df.groupby("date").size().reset_index(name="count")
        
        fig_timeline = px.line(
            daily_count,
            x="date",
            y="count",
            title="시간에 따른 지진 발생 추세",
            labels={"date": "날짜", "count": "지진 수"},
            markers=True
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # 상위 지진
        st.markdown("#### 🔴 가장 큰 규모의 지진 TOP 10")
        top_earthquakes = earthquakes_df.nlargest(10, "magnitude")[
            ["time", "magnitude", "place", "depth"]
        ].copy()
        top_earthquakes["time"] = top_earthquakes["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        top_earthquakes = top_earthquakes.rename(columns={
            "time": "시간",
            "magnitude": "규모",
            "place": "위치",
            "depth": "깊이(km)"
        })
        st.dataframe(top_earthquakes, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("전체 데이터")
        
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
        
        st.dataframe(display_df, use_container_width=True)
        
        # CSV 다운로드
        csv = display_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 CSV로 다운로드",
            data=csv,
            file_name=f"earthquakes_{start_year}_{end_year}.csv",
            mime="text/csv"
        )

# 푸터
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
    📊 데이터 출처: <a href='https://www.usgs.gov/programs/VHP/volcanic_rocks.html' target='_blank'>USGS Earthquake Hazards Program</a><br>
    🔄 데이터는 1시간마다 자동 갱신됩니다.
    </div>
    """, unsafe_allow_html=True)
