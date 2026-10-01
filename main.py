import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 예측기", layout="wide")
st.title("🌡️ 서울 연평균 기온 예측 및 상승률 비교기")

# 1. 데이터 불러오기 및 전처리
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"

@st.cache_data
def load_and_process_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    df["날짜"] = pd.to_datetime(df["날짜"].str.strip())
    df["연도"] = df["날짜"].dt.year
    
    yearly_summary = df.groupby("연도").agg(
        관측일수=("평균기온", "count"),
        연평균기온=("평균기온", "mean")
    ).reset_index()
    
    # 필터링 조건: 2025년 이하 & 관측일 300일 이상
    filtered_df = yearly_summary[
        (yearly_summary["연도"] <= 2025) & (yearly_summary["관측일수"] >= 300)
    ].copy()
    
    return filtered_df

df_filtered = load_and_process_data()

# 2. 선형 회귀 계산 함수
# 독립변수 X는 1908년부터의 경과 연수
df_filtered["X"] = df_filtered["연도"] - 1908

# [전체 기간 모델]
X_all = df_filtered["X"].values
y_all = df_filtered["연평균기온"].values
slope_all, intercept_all = np.polyfit(X_all, y_all, 1)

# [최근 20년 모델]
latest_end_year = int(df_filtered["연도"].max())
df_recent20 = df_filtered[df_filtered["연도"] > (latest_end_year - 20)].copy()
X_recent = df_recent20["X"].values
y_recent = df_recent20["연평균기온"].values
slope_recent, intercept_recent = np.polyfit(X_recent, y_recent, 1)

# 100년당 상승 온도 변환 (기울기 * 100)
rate_all_100y = slope_all * 100
rate_recent_100y = slope_recent * 100

# 3. 요약 정보 및 100년당 기온 상승률 비교 표시
start_year = int(df_filtered["연도"].min())
end_year = int(df_filtered["연도"].max())
total_years = len(df_filtered)

st.subheader("📊 데이터 기본 정보")
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("분석 대상 연도 수", f"{total_years}개 해")
col_info2.metric("시작 연도", f"{start_year}년")
col_info3.metric("끝 연도", f"{end_year}년")

st.markdown("---")

st.subheader("🔥 100년당 기온 상승률 비교")
col_m1, col_m2 = st.columns(2)

with col_m1:
    st.metric(
        label=f"🌐 전체 기간 ({start_year}~{end_year}년)",
        value=f"{rate_all_100y:+.2f} °C / 100년",
        help="전체 관측 데이터로 계산한 100년당 기온 변화량입니다."
    )

with col_m2:
    recent_start = int(df_recent20["연도"].min())
    diff_rate = rate_recent_100y - rate_all_100y
    st.metric(
        label=f"⚡ 최근 20년 ({recent_start}~{end_year}년)",
        value=f"{rate_recent_100y:+.2f} °C / 100년",
        delta=f"전체 대비 {diff_rate:+.2f} °C 빠른 상승률",
        delta_color="normal"
    )

st.markdown("---")

# 4. 연도 선택 및 기온 예측
st.subheader("🔮 연도별 예상 기온 (전체 기간 모델 기준)")
target_year = st.slider("연도를 선택하세요", min_value=1900, max_value=2100, value=2026, step=1)

predicted_temp_all = slope_all * (target_year - 1908) + intercept_all
predicted_temp_recent = slope_recent * (target_year - 1908) + intercept_recent

col_p1, col_p2 = st.columns(2)
col_p1.metric(f"🎯 전체 추세 기준 {target_year}년 예상 기온", f"{predicted_temp_all:.2f} °C")
col_p2.metric(f"🚀 최근 20년 추세 기준 {target_year}년 예상 기온", f"{predicted_temp_recent:.2f} °C")

st.markdown("---")

# 5. Plotly 시각화 (산점도 + 회귀선 2개)
line_years = np.arange(1900, 2101)
line_X = line_years - 1908
line_y_all = slope_all * line_X + intercept_all
line_y_recent = slope_recent * line_X + intercept_recent

fig = go.Figure()

# 실제 데이터 산점도
fig.add_trace(go.Scatter(
    x=df_filtered["연도"],
    y=df_filtered["연평균기온"],
    mode="markers",
    name="실제 연평균 기온",
    marker=dict(color="steelblue", size=7, opacity=0.7),
    hovertemplate="%{x}년: %{y:.2f}°C<extra></extra>"
))

# 전체 기간 회귀선
fig.add_trace(go.Scatter(
    x=line_years,
    y=line_y_all,
    mode="lines",
    name=f"전체 추세선 ({rate_all_100y:+.2f}°C/100년)",
    line=dict(color="crimson", width=2, dash="dash"),
    hovertemplate="%{x}년 예상(전체): %{y:.2f}°C<extra></extra>"
))

# 최근 20년 회귀선
fig.add_trace(go.Scatter(
    x=line_years,
    y=line_y_recent,
    mode="lines",
    name=f"최근 20년 추세선 ({rate_recent_100y:+.2f}°C/100년)",
    line=dict(color="darkorange", width=2.5),
    hovertemplate="%{x}년 예상(최근20년): %{y:.2f}°C<extra></extra>"
))

# 선택된 연도 하이라이트 (전체 추세선 기준)
fig.add_trace(go.Scatter(
    x=[target_year],
    y=[predicted_temp_all],
    mode="markers",
    name=f"선택 연도 ({target_year})",
    marker=dict(color="gold", size=14, symbol="star", line=dict(color="black", width=1)),
    hovertemplate=f"선택: {target_year}년<br>예상 기온: {predicted_temp_all:.2f}°C<extra></extra>"
))

fig.update_layout(
    title="서울 연평균 기온 및 추세 비교 (전체 vs 최근 20년)",
    xaxis_title="연도",
    yaxis_title="평균기온 (°C)",
    xaxis=dict(range=[1895, 2105], dtick=20),
    hovermode="closest",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)
