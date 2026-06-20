import streamlit as st

st.set_page_config(
    page_title="🌍 Global Earthquake Visualization",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Global Earthquake Visualization")

st.markdown("""
### USGS 실시간 지진 데이터 시각화

왼쪽 사이드바에서 원하는 페이지를 선택하세요! 👈

---

#### 📌 제공 기능
- 🗺️ **지진 분포 지도**: 연도별 지진을 인터랙티브 지도에 시각화
- 📊 **통계 분석**: 규모, 깊이, 시간 추세 분석
- 📋 **데이터 조회**: 전체 지진 데이터 및 CSV 다운로드

#### 🔧 사용 방법
1. 왼쪽 사이드바에서 페이지 선택
2. 원하는 연도 범위 설정
3. 지진 규모 필터링
4. 지도와 차트로 데이터 분석

---

**📊 데이터 출처**: [USGS Earthquake Hazards Program](https://www.usgs.gov/)
""")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🗺️ 지도", "인터랙티브")

with col2:
    st.metric("📊 분석", "실시간 데이터")

with col3:
    st.metric("📥 다운로드", "CSV 가능")
