import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 예측기", layout="wide")
st.title("🌡️ 서울 연평균 기온 예측기")

# 1. 데이터 불러오기 및 전처리
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"

@st.cache_data
def load_and_process_data():
    # UTF-8 인코딩으로 데이터 로드
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    
    # 날짜 컬럼을 datetime 형식으로 변환 후 연도 추출
    df["날짜"] = pd.to_datetime(df["날짜"].str.strip())
    df["연도"] = df["날짜"].dt.year
    
    # 관측일수 및 평균기온 계산 (결측치 제외)
    yearly_summary = df.groupby("연도").agg(
        관측일수=("평균기온", "count"),
        연평균기온=("평균기온", "mean")
    ).reset_index()
    
    # 조건 적용: 2025년 이하 & 관측일 300일 이상
    filtered_df = yearly_summary[
        (yearly_summary["연도"] <= 2025) & (yearly_summary["관측일수"] >= 300)
    ].copy()
    
    return filtered_df

df_filtered = load_and_process_data()

# 2. 선형 회귀 분석 (1908년부터 경과한 연수를 독립변수로 설정)
# X = 연도 - 1908
df_filtered["X"] = df_filtered["연도"] - 1908
X = df_filtered["X"].values
y = df_filtered["연평균기온"].values

# 1차 선형 회귀 계수 (기울기, 절편)
slope, intercept = np.polyfit(X, y, 1)

# 상관계수 계산
corr = np.corrcoef(df_filtered["연도"], y)[0, 1]

# 3. 요약 정보 출력
start_year = int(df_filtered["연도"].min())
end_year = int(df_filtered["연도"].max())
total_years = len(df_filtered)

st.subheader("📊 데이터 분석 요약")
col1, col2, col3, col4 = st.columns(4)
col1.metric("분석 대상 연도 수", f"{total_years}개 해")
col2.metric("시작 연도", f"{start_year}년")
col3.metric("끝 연도", f"{end_year}년")
col4.metric("상관계수 (r)", f"{corr:.4f}")

st.markdown("---")

# 4. 연도 선택 슬라이더 및 예상 기온 예측
st.subheader("🔮 미래/과거 기온 예측")
target_year = st.slider("연도를 선택하세요", min_value=1900, max_value=2100, value=2026, step=1)

# 예측 계산: y = slope * (target_year - 1908) + intercept
predicted_temp = slope * (target_year - 1908) + intercept

st.metric(
    label=f"🎯 {target_year}년 예상 연평균 기온",
    value=f"{predicted_temp:.2f} °C"
)

st.markdown("---")

# 5. Plotly 시각화 (산점도 + 회귀선)
# 추세선을 전체 연도 범위(1900~2100)로 확장하여 생성
line_years = np.arange(1900, 2101)
line_X = line_years - 1908
line_y = slope * line_X + intercept

fig = go.Figure()

# 실제 데이터 산점도
fig.add_trace(go.Scatter(
    x=df_filtered["연도"],
    y=df_filtered["연평균기온"],
    mode="markers",
    name="실제 연평균 기온",
    marker=dict(color="royalblue", size=7),
    hovertemplate="%{x}년: %{y:.2f}°C<extra></extra>"
))

# 회귀 직선
fig.add_trace(go.Scatter(
    x=line_years,
    y=line_y,
    mode="lines",
    name="회귀 직선",
    line=dict(color="firebrick", width=2, dash="dash"),
    hovertemplate="%{x}년 예상: %{y:.2f}°C<extra></extra>"
))

# 슬라이더로 선택한 연도 위치 하이라이트
fig.add_trace(go.Scatter(
    x=[target_year],
    y=[predicted_temp],
    mode="markers",
    name=f"선택 연도 ({target_year})",
    marker=dict(color="gold", size=14, symbol="star", line=dict(color="black", width=1)),
    hovertemplate=f"선택: {target_year}년<br>예상 기온: {predicted_temp:.2f}°C<extra></extra>"
))

fig.update_layout(
    title="서울 연평균 기온 변화 및 추세선 (1908년 기준 경과 연수 모델)",
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    xaxis=dict(range=[1895, 2105], dtick=20),
    hovermode="closest",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)
