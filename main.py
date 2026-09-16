import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="남양주시 버스 배차 시간 분석",
    page_icon="🚌",
    layout="wide"
)

st.title("🚌 남양주시 버스 노선 배차 시간 분석")
st.markdown("남양주시 버스 노선의 **평일 배차 시간**과 **주말 배차 시간**의 분포를 히스토그램으로 확인합니다.")

# 데이터 로드 함수
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/happykth/data/main/namyangju_bus.csv"
    try:
        df = pd.read_csv(url)
    except Exception:
        df = pd.read_csv(url, encoding='cp949')
    return df

with st.spinner("데이터를 불러오는 중입니다..."):
    df = load_data()

st.sidebar.header("🔍 설정 및 필터")

cols = df.columns.tolist()

# 평일/주말 배차시간 컬럼 자동 감지
weekday_col = next((c for c in cols if '평일' in c and ('배차' in c or '시간' in c or '간격' in c)), None)
weekend_col = next((c for c in cols if ('주말' in c or '휴일' in c or '토요일' in c) and ('배차' in c or '시간' in c or '간격' in c)), None)

# 자동 감지 실패 시 수동 선택
if not weekday_col or not weekend_col:
    numeric_cols = df.select_dtypes(include=['number', 'object']).columns.tolist()
    weekday_col = st.sidebar.selectbox("평일 배차시간 컬럼 선택", numeric_cols, index=0)
    weekend_col = st.sidebar.selectbox("주말 배차시간 컬럼 선택", numeric_cols, index=min(1, len(numeric_cols)-1))
else:
    st.sidebar.write(f"**자동 감지된 평일 컬럼:** `{weekday_col}`")
    st.sidebar.write(f"**자동 감지된 주말 컬럼:** `{weekend_col}`")

# 데이터 전처리 (숫자 추출 및 변환)
df_clean = df.copy()
df_clean[weekday_col] = pd.to_numeric(df_clean[weekday_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
df_clean[weekend_col] = pd.to_numeric(df_clean[weekend_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce')

# 슬라이더 필터 옵션
max_val = int(max(df_clean[weekday_col].dropna().max() if not df_clean[weekday_col].dropna().empty else 180,
                  df_clean[weekend_col].dropna().max() if not df_clean[weekend_col].dropna().empty else 180))

bins = st.sidebar.slider("히스토그램 구간(Bin) 개수", min_value=5, max_value=50, value=20, step=5)
range_filter = st.sidebar.slider("배차 시간 범위 지정 (분)", 0, max_val, (0, max_val))

filtered_df = df_clean[
    (df_clean[weekday_col] >= range_filter[0]) & (df_clean[weekday_col] <= range_filter[1]) |
    (df_clean[weekend_col] >= range_filter[0]) & (df_clean[weekend_col] <= range_filter[1])
]

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 배차 시간 히스토그램", "📈 평일 vs 주말 비교", "📋 원본 데이터"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 평일 배차 시간 빈도수")
        fig_weekday = px.histogram(
            filtered_df, 
            x=weekday_col, 
            nbins=bins,
            title="평일 배차 시간 분포",
            labels={weekday_col: "배차 시간 (분)", "count": "노선 수"},
            color_discrete_sequence=['#1f77b4']
        )
        fig_weekday.update_layout(bargap=0.1, yaxis_title="노선 수(개)", xaxis_title="배차 시간(분)")
        st.plotly_chart(fig_weekday, use_container_width=True)
        st.metric("평일 평균 배차 시간", f"{filtered_df[weekday_col].mean():.1f} 분")

    with col2:
        st.subheader("🏖️ 주말 배차 시간 빈도수")
        fig_weekend = px.histogram(
            filtered_df, 
            x=weekend_col, 
            nbins=bins,
            title="주말 배차 시간 분포",
            labels={weekend_col: "배차 시간 (분)", "count": "노선 수"},
            color_discrete_sequence=['#ff7f0e']
        )
        fig_weekend.update_layout(bargap=0.1, yaxis_title="노선 수(개)", xaxis_title="배차 시간(분)")
        st.plotly_chart(fig_weekend, use_container_width=True)
        st.metric("주말 평균 배차 시간", f"{filtered_df[weekend_col].mean():.1f} 분")

with tab2:
    st.subheader("⚖️ 평일 vs 주말 배차 시간 중첩 비교")
    fig_compare = go.Figure()
    fig_compare.add_trace(go.Histogram(
        x=filtered_df[weekday_col], 
        name="평일", 
        opacity=0.6,
        marker_color='#1f77b4',
        nbinsx=bins
    ))
    fig_compare.add_trace(go.Histogram(
        x=filtered_df[weekend_col], 
        name="주말", 
        opacity=0.6,
        marker_color='#ff7f0e',
        nbinsx=bins
    ))
    fig_compare.update_layout(
        barmode='overlay',
        title="평일과 주말 배차 시간 분포 비교",
        xaxis_title="배차 시간 (분)",
        yaxis_title="노선 수 (개)",
        bargap=0.1
    )
    st.plotly_chart(fig_compare, use_container_width=True)

with tab3:
    st.subheader("📄 남양주시 버스 노선 원본 데이터")
    st.dataframe(df, use_container_width=True)
