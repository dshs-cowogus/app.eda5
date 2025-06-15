import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 지역명 매핑 (KOR → ENG) – Population 분석용
# ---------------------
REGION_MAP = {
    "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
    "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
    "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
    "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
    "제주": "Jeju",
}

# ==============================================================================
#  페이지 클래스 정의
# ==============================================================================

class Home:
    """🏠 홈 페이지 – 데이터셋 소개 등"""

    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        ## Bike Sharing Demand 데이터셋
        - Source: [Kaggle Competition](https://www.kaggle.com/c/bike-sharing-demand)
        - Records hourly bike rentals in Washington D.C. (2011–2012)
        - Key columns: `datetime`, `season`, `holiday`, `workingday`, `weather`, `temp`, `atemp`, `humidity`, `windspeed`, `casual`, `registered`, `count`
        """)

class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user["idToken"]

                # Firestore 사용자 정보 로드
                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1); st.rerun()
            except Exception:
                st.error("로그인 실패")

class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")
        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email, "name": name, "gender": gender,
                    "phone": phone, "role": "user", "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1); st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1); st.rerun()
            except Exception:
                st.error("이메일 전송 실패")

class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")
        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"],
                               index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함")))
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email, "name": name, "gender": gender,
                "phone": phone, "profile_image_url": st.session_state.get("profile_image_url", "")
            })
            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1); st.rerun()

class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1); st.rerun()

# ==============================================================================
#  EDA 페이지 (Bike Sharing + Population Trends)
# ==============================================================================
class EDA:
    """EDA 페이지 – 두 데이터셋(Bike, Population)을 탭으로 제공"""

    def __init__(self):
        st.title("📊 Exploratory Data Analysis")
        main_tabs = st.tabs(["Bike-Sharing", "Population-Trends"])
        with main_tabs[0]:
            self._bike_sharing_eda()
        with main_tabs[1]:
            self._population_trends_eda()

    # ------------------------------------------------------------------
    #  Bike Sharing EDA (원본 8탭)
    # ------------------------------------------------------------------
    def _bike_sharing_eda(self):
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv", key="bike_csv")
        if uploaded is None:
            st.info("train.csv 파일을 업로드 해주세요."); return
        df = pd.read_csv(uploaded, parse_dates=["datetime"])

        tabs = st.tabs([
            "1. 목적 & 절차", "2. 데이터셋 설명", "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출", "5. 시각화", "6. 상관관계 분석",
            "7. 이상치 제거", "8. 로그 변환"
        ])

        # ---------------- 1. 목적 & 절차 ----------------
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터셋을 탐색해
            각 특성이 `count`(대여량)에 미치는 영향을 이해한다.

            **절차**:
            1. 구조 및 기초 통계 확인
            2. 품질 점검 (결측/중복)
            3. `datetime` 파생 특성 생성
            4. 시각화 탐색
            5. 상관분석
            6. 이상치 탐지
            7. 분포 안정화를 위한 로그 변환
            """)

        # ---------------- 2. 데이터셋 설명 ----------------
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"""
            - 총 관측치: {df.shape[0]:,}개 / 피처: {df.shape[1]}개
            - 주요 피처 설명은 홈 페이지 참고.
            """)
            st.subheader("df.info()")
            buf = io.StringIO(); df.info(buf=buf); st.text(buf.getvalue())
            st.subheader("df.describe()")
            st.dataframe(df.describe())
            st.subheader("샘플(첫 5행)"); st.dataframe(df.head())

        # ---------------- 3. 품질 체크 ----------------
        with tabs[2]:
            st.header("📥 품질 체크")
            st.subheader("결측값 개수"); st.bar_chart(df.isnull().sum())
            st.write(f"중복 행: {df.duplicated().sum():,}개")

        # ---------------- 4. Datetime ----------------
        with tabs[3]:
            st.header("🕒 Datetime 특성")
            for col in ["year", "month", "day", "hour", "dayofweek"]:
                if col not in df.columns:
                    df[col] = getattr(df["datetime"].dt, col)
            st.dataframe(df[["datetime", "year", "month", "day", "hour", "dayofweek"]].head())

        # ---------------- 5. 시각화 ----------------
        with tabs[4]:
            st.header("📈 시각화")
            # 근무일별 시간대 평균
            st.subheader("Workingday vs Hour")
            fig, ax = plt.subplots(); sns.pointplot(x="hour", y="count", hue="workingday", data=df, ax=ax)
            st.pyplot(fig)
            # 요일별
            st.subheader("Weekday vs Hour")
            fig2, ax2 = plt.subplots(); sns.pointplot(x="hour", y="count", hue="dayofweek", data=df, ax=ax2)
            st.pyplot(fig2)
            # 시즌별
            st.subheader("Season vs Hour")
            fig3, ax3 = plt.subplots(); sns.pointplot(x="hour", y="count", hue="season", data=df, ax=ax3)
            st.pyplot(fig3)
            # 날씨별
            st.subheader("Weather vs Hour")
            fig4, ax4 = plt.subplots(); sns.pointplot(x="hour", y="count", hue="weather", data=df, ax=ax4)
            st.pyplot(fig4)

        # ---------------- 6. 상관관계 ----------------
        with tabs[5]:
            st.header("🔗 상관관계")
            corr_df = df[["temp", "atemp", "humidity", "windspeed", "casual", "registered", "count"]].corr()
            st.dataframe(corr_df)
            fig, ax = plt.subplots(figsize=(7, 5)); sns.heatmap(corr_df, annot=True, ax=ax, cmap="coolwarm"); st.pyplot(fig)

        # ---------------- 7. 이상치 제거 ----------------
        with tabs[6]:
            st.header("🚫 이상치")
            mean, std = df["count"].mean(), df["count"].std(); upper = mean + 3*std
            st.write(f"기준: {upper:,.0f} (> mean+3σ)")
            st.write(f"제거 전: {len(df):,}, 제거 후: {len(df[df['count']<=upper]):,}")

        # ---------------- 8. 로그 변환 ----------------
        with tabs[7]:
            st.header("🔄 로그 변환")
            df["log_count"] = np.log1p(df["count"])
            fig, axs = plt.subplots(1, 2, figsize=(12, 4))
            sns.histplot(df["count"], ax=axs[0]); axs[0].set_title("Original")
            sns.histplot(df["log_count"], ax=axs[1]); axs[1].set_title("Log")
            st.pyplot(fig)

    # ------------------------------------------------------------------
    #  Population Trends EDA (신규)
    # ------------------------------------------------------------------
    def _population_trends_eda(self):
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv", key="pop_csv")
        if uploaded is None:
            st.info("population_trends.csv 파일을 업로드 해주세요."); return
        df = pd.read_csv(uploaded)

        # 전처리 (세종 '-' → 0, 숫자 변환)
        num_cols = ["인구", "출생아수(명)", "사망자수(명)"]
        df.loc[df["지역"] == "세종", num_cols] = df.loc[df["지역"] == "세종", num_cols].replace("-", 0)
        for col in num_cols:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False).str.replace("-", "0").astype(int)

        tabs = st.tabs(["Basic-Stats", "Year-Trend", "Regional-Rank", "Change-Top100", "Area-Chart"])

        # 1) Basic
        with tabs[0]:
            st.subheader("DataFrame Info"); buf = io.StringIO(); df.info(buf=buf); st.text(buf.getvalue())
            st.subheader("Describe"); st.dataframe(df.describe())

        # 2) Year Trend
        with tabs[1]:
            nation = df[df["지역"] == "전국"].sort_values("연도")
            fig, ax = plt.subplots(); sns.lineplot(data=nation, x="연도", y="인구", marker="o", ax=ax)
            ax.set_title("Total Population"); ax.set_xlabel("Year"); ax.set_ylabel("Population")
            latest = nation["연도"].max(); recent = nation[nation["연도"] >= latest-2]
            recent["net"] = recent["출생아수(명)"] - recent["사망자수(명)"]
            avg_net = recent["net"].mean()
            fut_years = list(range(latest+1, 2036)); pred = [nation.iloc[-1]["인구"]]
            for _ in fut_years: pred.append(pred[-1] + avg_net); pred.pop(0)
            ax.plot(fut_years, pred, ls="--", marker="x", label="Projected"); ax.legend(); st.pyplot(fig)
            st.write(f"Avg net change (last 3y): {avg_net:,.0f}/yr")

        # 3) Regional Rank (최근5).
        with tabs[2]:
            yr_max = df["연도"].max(); prev_year = yr_max-5
            now = df[df["연도"] == yr_max][["지역", "인구"]].rename(columns={"인구":"현재"})
            past = df[df["연도"] == prev_year][["지역", "인구"]].rename(columns={"인구":"5년전"})
            comp = now.merge(past, on="지역"); comp = comp[comp["지역"] != "전국"]
            comp["Δ"] = comp["현재"]-comp["5년전"]
            comp["rate"] = comp["Δ"] / comp["5년전"] * 100
            comp["Region"] = comp["지역"].map(REGION_MAP)
            comp = comp.sort_values("Δ", ascending=False)
            fig1, ax1 = plt.subplots(figsize=(8,6)); sns.barplot(data=comp, x="Δ", y="Region", orient="h", ax=ax1)
            for i,v in enumerate(comp["Δ"]): ax1.text(v, i, f"{v/1000:,.0f}k", va="center", ha="left")
            ax1.set_xlabel("Δ Pop (k)"); st.pyplot(fig1)
            fig2, ax2 = plt.subplots(figsize=(8,6)); sns.barplot(data=comp, x="rate", y="Region", orient="h", ax=ax2, palette="viridis")
            for i,v in enumerate(comp["rate"]): ax2.text(v, i, f"{v:.1f}%", va="center", ha="left")
            ax2.set_xlabel("Rate (%)"); st.pyplot(fig2)

        # 4) Change Top100
        with tabs[3]:
            diff_df = df.sort_values(["지역","연도"]).groupby("지역").apply(lambda x: x.assign(diff=x["인구"].diff())).reset_index(drop=True)
            diff_df = diff_df[diff_df["지역"] != "전국"].dropna()
            top100 = diff_df.loc[diff_df["diff"].abs().nlargest(100).index]
            top100["Region"] = top100["지역"].map(REGION_MAP)
            styled = (top100[["연도","Region","인구","diff"]]
                      .style.format({"인구":"{:,}", "diff":"{:,}"})
                      .background_gradient(subset=["diff"], cmap="RdBu", vmin=-top100["diff"].abs().max(), vmax=top100["diff"].abs().max()))
            st.dataframe(styled, use_container_width=True, height=600)

        # 5) Stacked Area
        with tabs[4]:
            pivot = df.pivot(index="연도", columns="지역", values="인구").drop(columns=["전국"])
            pivot = pivot.rename(columns=REGION_MAP)/1000
            fig, ax = plt.subplots(figsize=(10,6)); pivot.plot.area(ax=ax, cmap="tab20")
            ax.set_xlabel("Year"); ax.set_ylabel("Population (k)"); ax.set_title("Regional Composition")
            ax.legend(loc="upper left", bbox_to_anchor=(1,1)); st.pyplot(fig)

# ==============================================================================
#  페이지 객체 & 네비게이션
# ==============================================================================
Page_Login    = st.Page(Login, title="Login", icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
