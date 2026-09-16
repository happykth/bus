import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="남양주시 버스 배차 시간 분석",
    page_icon="🚌",
    layout="wide"
)

st.title("🚌 남양주시 버스 노선 배차 시간 및 인가거리 분석")
st.markdown("남양주시 버스 노선의 **배차 시간 분포**, **인가거리 상위 노선**, 그리고 **인가거리와 배차 시간 간의 관계**를 확인합니다.")

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

# 컬럼 자동 탐지
weekday_col = next((c for c in cols if '평일' in c and ('배차' in c or '시간' in c or '간격' in c)), None)
weekend_col = next((c for c in cols if ('주말' in c or '휴일' in c or '토요일' in c) and ('배차' in c or '시간' in c or '간격' in c)), None)
distance_col = next((c for c in cols if '거리' in c or '인가거리' in c or '운행거리' in c), None)
route_col = next((c for c in cols if '노선' in c or '버스' in c or '명' in c), cols[0] if cols else None)

# 수동 선택 UI (자동 탐지 실패 대비)
if not weekday_col or not weekend_col:
    numeric_cols = df.select_dtypes(include=['number', 'object']).columns.tolist()
    weekday_col = st.sidebar.selectbox("평일 배차시간 컬럼 선택", numeric_cols, index=0)
    weekend_col = st.sidebar.selectbox("주말 배차시간 컬럼 선택", numeric_cols, index=min(1, len(numeric_cols)-1))

if not distance_col:
    distance_col = st.sidebar.selectbox("인가거리 컬럼 선택", cols)

if not route_col:
    route_col = st.sidebar.selectbox("노선명 컬럼 선택", cols)

st.sidebar.write(f"**평일 컬럼:** `{weekday_col}`")
st.sidebar.write(f"**주말 컬럼:** `{weekend_col}`")
st.sidebar.write(f"**거리 컬럼:** `{distance_col}`")

# 데이터 전처리 (숫자형 변환)
df_clean = df.copy()
df_clean[weekday_col] = pd.to_numeric(df_clean[weekday_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
df_clean[weekend_col] = pd.to_numeric(df_clean[weekend_col].astype(str).str.extract(r'(\d+)')[0], errors='coerce')

# 거리 컬럼 숫자 변환 (소수점 포함)
df_clean[distance_col] = pd.to_numeric(df_clean[distance_col].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce')

# 슬라이더 필터
max_val = int(max(df_clean[weekday_col].dropna().max() if not df_clean[weekday_col].dropna().empty else 180,
                  df_clean[weekend_col].dropna().max() if not df_clean[weekend_col].dropna().empty else 180))

bins = st.sidebar.slider("히스토그램 구간(Bin) 개수", min_value=5, max_value=50, value=20, step=5)
range_filter = st.sidebar.slider("배차 시간 범위 지정 (분)", 0, max_val, (0, max_val))

# 데이터 필터링
filtered_df = df_clean[
    (df_clean[weekday_col] >= range_filter[0]) & (df_clean[weekday_col] <= range_filter[1]) |
    (df_clean[weekend_col] >= range_filter[0]) & (df_clean[weekend_col] <= range_filter[1])
]

# Tab 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 배차 시간 히스토그램", 
    "📈 평일 vs 주말 비교", 
    "🛣️ 인가거리 상위 10개 노선", 
    "🔵 인가거리 vs 평일배차 관계", 
    "📋 원본 데이터"
])

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
    st.subheader("🛣️ 인가거리가 가장 긴 상위 10개 노선")
    
    top10_df = df_clean.dropna(subset=[distance_col]).sort_values(by=distance_col, ascending=False).head(10)
    top10_df[route_col] = top10_df[route_col].astype(str)
    
    fig_bar = px.bar(
        top10_df,
        x=distance_col,
        y=route_col,
        orientation='h',
        text=distance_col,
        title="인가거리 Top 10 노선 (km)",
        labels={distance_col: "인가거리 (km)", route_col: "노선명"},
        color=distance_col,
        color_continuous_scale='Reds'
    )
    fig_bar.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="인가거리 (km)",
        yaxis_title="노선명",
        coloraxis_showscale=False
    )
    fig_bar.update_traces(texttemplate='%{text:.1f} km', textposition='outside')
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("##### 📌 상위 10개 노선 상세 정보")
    st.dataframe(top10_df[[route_col, distance_col, weekday_col, weekend_col]], use_container_width=True)

with tab4:
    st.subheader("🔵 인가거리와 평일 배차 시간 간 상관관계 분석")
    
    # 결측치 제거
    scatter_df = filtered_df.dropna(subset=[distance_col, weekday_col])
    
    if len(scatter_df) > 0:
        # 산점도 기본 그래프 생성
        fig_scatter = px.scatter(
            scatter_df,
            x=distance_col,
            y=weekday_col,
            hover_name=route_col,
            title="인가거리 vs 평일 배차 시간 산점도",
            labels={distance_col: "인가거리 (km)", weekday_col: "평일 배차 시간 (분)"},
            color=weekday_col,
            color_continuous_scale='Viridis'
        )
        
        # numpy를 이용해 외부 패키지 없이 추세선(OLS) 계산
        x_vals = scatter_df[distance_col].values
        y_vals = scatter_df[weekday_col].values
        
        if len(x_vals) > 1:
            slope, intercept = np.polyfit(x_vals, y_vals, 1)
            x_range = np.linspace(x_vals.min(), x_vals.max(), 100)
            y_range = slope * x_range + intercept
            
            # 추세선 추적 추가
            fig_scatter.add_trace(go.Scatter(
                x=x_range,
                y=y_range,
                mode='lines',
                name='추세선 (OLS)',
                line=dict(color='red', width=2, dash='dash')
            ))
        
        fig_scatter.update_layout(
            xaxis_title="인가거리 (km)",
            yaxis_title="평일 배차 시간 (분)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 상관계수 계산
        corr = scatter_df[distance_col].corr(scatter_df[weekday_col])
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("피어슨 상관계수 (r)", f"{corr:.3f}")
        with col_s2:
            if abs(corr) >= 0.7:
                corr_text = "매우 강한 상관관계"
            elif abs(corr) >= 0.5:
                corr_text = "강한 상관관계"
            elif abs(corr) >= 0.3:
                corr_text = "뚜렷한 상관관계"
            else:
                corr_text = "약하거나 거의 없는 상관관계"
            st.info(f"💡 **분석 결과:** 두 변수 간에는 **{corr_text}**가 관찰됩니다.")
    else:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")

with tab5:
    st.subheader("📄 남양주시 버스 노선 원본 데이터")
    st.dataframe(df, use_container_width=True)
