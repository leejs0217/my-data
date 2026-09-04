import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="서울 연평균 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 연평균 기온 변화")
st.write("서울의 기온 데이터를 이용하여 약 100년 동안 연평균 기온이 어떻게 변해 왔는지 살펴봅니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    return df

try:
    df = load_data()

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온을 숫자로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 연도 열 만들기
    df["연도"] = df["날짜"].dt.year

    # 연도별 평균기온 계산
    yearly_temp = (
        df.dropna(subset=["연도", "평균기온"])
        .groupby("연도")["평균기온"]
        .mean()
        .reset_index()
    )

    # 소수점 둘째 자리까지 표시
    yearly_temp["평균기온"] = yearly_temp["평균기온"].round(2)

    # 전체 데이터 정보
    st.subheader("📊 데이터 개요")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("전체 데이터 개수", f"{len(df):,}개")

    with col2:
        st.metric(
            "분석 연도",
            f"{yearly_temp['연도'].min()} ~ {yearly_temp['연도'].max()}"
        )

    with col3:
        st.metric("분석 연도 수", f"{len(yearly_temp):,}년")

    # 연평균 기온 그래프
    st.subheader("📈 서울 연평균 기온 변화")

    chart_data = yearly_temp.set_index("연도")

    st.line_chart(
        chart_data,
        y="평균기온",
        x_label="연도",
        y_label="평균기온(℃)"
    )

    st.caption(
        "※ 각 연도의 일평균 기온을 평균하여 연평균 기온을 계산했습니다."
    )

    # 요약 통계
    st.subheader("📋 원본 데이터 요약 통계")

    stat_data = df[["평균기온", "최저기온", "최고기온"]].copy()

    # 숫자형으로 변환
    for column in stat_data.columns:
        stat_data[column] = pd.to_numeric(
            stat_data[column],
            errors="coerce"
        )

    summary = pd.DataFrame({
        "개수": stat_data.count(),
        "평균": stat_data.mean(),
        "최소": stat_data.min(),
        "최대": stat_data.max()
    }).round(2)

    summary.index.name = "기온 항목"

    st.dataframe(
        summary,
        use_container_width=True
    )

    # 연도별 데이터
    with st.expander("연도별 연평균 기온 데이터 보기"):
        st.dataframe(
            yearly_temp,
            use_container_width=True
        )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.write("오류 내용:", e)
