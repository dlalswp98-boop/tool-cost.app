import streamlit as st
import math
import pandas as pd
import plotly.express as px
import socket
import qrcode
from io import BytesIO

# 기본 세팅
st.set_page_config(page_title="공구비 산출기 v6", page_icon="🛠️", layout="wide")
st.title("🛠️ 공구비 산출 프로그램 v6")

# 세션 상태 초기화
if "tools" not in st.session_state:
    st.session_state.tools = []

# 유틸 함수
def nceil(x):
    return int(math.ceil(x))

def safe(x, d=0.0):
    try:
        v = float(x)
        if math.isnan(v):
            return d
        return v
    except:
        return d

# 화면 3분할
col1, col2, col3 = st.columns([1.1, 1.2, 1.2], gap="large")

# ----------------------------
# 1) 좌측 입력 영역
# ----------------------------
with col1:
    st.subheader("입력 / 공구 추가")

    basis = st.radio("기준 선택", ["거리(m)", "홀수(개)"], horizontal=True)
    ap_global = st.number_input("절입깊이 ap (m/홀)", value=0.03, format="%.6f")

    if basis == "거리(m)":
        total_m = st.number_input("가공거리(m)", value=30.0)
        total_holes = nceil(total_m / max(1e-9, ap_global))
    else:
        total_holes = st.number_input("홀수(개)", value=1000)
        total_m = total_holes * ap_global

    st.caption(f"총 {total_m:.3f} m / {total_holes:,} 홀")

    # 공구 추가 버튼
    if st.button("➕ 공구 추가"):
        st.session_state.tools.append({
            "name": "",
            "type": "인덱서블",
            "임율": 350,
            "vc": 0,
            "fn": 0,
            "ap": ap_global,
            "동시": 2,
            "코너": 2,
            "코너수명": 0,
            "인써트가": 0,
            "홀더가": 0,
            "홀더비": 15,
            "TS수명": 0,
            "TS재연": 0,
            "TS재가": 0,
            "본체가": 0,
            "본체수명": 0,
            "재연마": 0,
            "재가격": 0,
            "회복": 1
        })
    # 공구별 입력창
    for i, t in enumerate(st.session_state.tools):
        with st.expander(f"공구 {i+1}", expanded=True if i == 0 else False):
            c1, c2 = st.columns(2)

            t["name"] = c1.text_input("공구명", t["name"], key=f"name{i}")
            t["type"] = c2.selectbox("종류", ["인덱서블", "탑솔리드 인덱서블", "솔리드"], key=f"type{i}")
            t["임율"] = c1.number_input("임율", value=float(t["임율"]), key=f"ims{i}")
            t["vc"] = c2.number_input("Vc", value=float(t["vc"]), key=f"vc{i}")
            t["fn"] = c1.number_input("fn", value=float(t["fn"]), key=f"fn{i}")
            t["ap"] = c2.number_input("ap", value=float(t["ap"]), key=f"ap_in{i}")

            # 인덱서블
            if t["type"] == "인덱서블":
                t["동시"] = c1.number_input("동시 인써트 수", value=int(t["동시"]), key=f"d{i}")
                t["코너"] = c2.number_input("코너 수", value=int(t["코너"]), key=f"k{i}")
                t["코너수명"] = c1.number_input("코너당 수명", value=float(t["코너수명"]), key=f"life{i}")
                t["인써트가"] = c2.number_input("인써트 가격", value=float(t["인써트가"]), key=f"ip{i}")
                t["홀더가"] = c1.number_input("홀더 가격", value=float(t["홀더가"]), key=f"hp{i}")
                t["홀더비"] = c2.number_input("인써트 N개당 홀더1", value=int(t["홀더비"]), key=f"hr{i}")

            # 탑솔리드 인덱서블
            elif t["type"] == "탑솔리드 인덱서블":
                t["TS수명"] = c1.number_input("인써트 수명", value=float(t["TS수명"]), key=f"ts{i}")
                t["TS재연"] = c2.number_input("재연마 횟수", value=int(t["TS재연"]), key=f"tsr{i}")
                t["TS재가"] = c1.number_input("재연마 가격", value=float(t["TS재가"]), key=f"tsg{i}")
                t["인써트가"] = c2.number_input("인써트 가격", value=float(t["인써트가"]), key=f"tsi{i}")
                t["홀더가"] = c1.number_input("홀더 가격", value=float(t["홀더가"]), key=f"tsh{i}")
                t["홀더비"] = c2.number_input("홀더비", value=int(t["홀더비"]), key=f"tshr{i}")

            # 솔리드 드릴
            else:
                t["본체가"] = c1.number_input("본체 가격", value=float(t["본체가"]), key=f"body{i}")
                t["본체수명"] = c2.number_input("본체 수명", value=float(t["본체수명"]), key=f"bodylife{i}")
                t["재연마"] = c1.number_input("재연마 횟수", value=int(t["재연마"]), key=f"rb{i}")
                t["재가격"] = c2.number_input("재연마 가격", value=float(t["재가격"]), key=f"rg{i}")
                t["회복"] = c1.number_input("재연마 수명 회복률", value=float(t["회복"]), key=f"rh{i}")

# ----------------------------
# 2) 중앙 결과 영역
# ----------------------------
with col2:
    st.subheader("결과값")
    calc_btn = st.button("계산하기")
    table = st.empty()

# ----------------------------
# 3) 우측 그래프 영역
# ----------------------------
with col3:
    st.subheader("그래프")
    chart = st.empty()
    qr_btn = st.button("QR 생성")
    qrbox = st.empty()


# --------------------------------------
# 계산 함수 정의
# --------------------------------------

def calc_indexable(m, t):
    life = safe(t["코너수명"]) * max(1, int(t["코너"]))
    life = max(life, 1e-9)
    need = nceil(m / life) * max(1, int(t["동시"]))
    holder = nceil(need / max(1, int(t["홀더비"])))
    cost = need * safe(t["인써트가"]) + holder * safe(t["홀더가"])
    return cost, need, holder


def calc_topsolid(m, t):
    eff = safe(t["TS수명"]) * (1 + max(0, int(t["TS재연"])))
    eff = max(eff, 1e-9)
    need = nceil(m / eff)
    holder = nceil(need / max(1, int(t["홀더비"])))
    cost = need * (safe(t["인써트가"]) + safe(t["TS재가"]) * max(0, int(t["TS재연"]))) \
           + holder * safe(t["홀더가"])
    return cost, need, holder


def calc_solid(m, t):
    base = safe(t["본체수명"])
    eff = base + max(0, int(t["재연마"])) * (base * safe(t["회복"]))
    eff = max(eff, 1e-9)
    need = nceil(m / eff)
    cost = need * (safe(t["본체가"]) + safe(t["재가격"]) * max(0, int(t["재연마"])))
    return cost, need, eff
# --------------------------------------
# 결과 계산 실행
# --------------------------------------

df = None

if calc_btn and st.session_state.tools:
    rows = []

    for t in st.session_state.tools:
        # --- 인덱서블 ---
        if t["type"] == "인덱서블":
            cost, u, h = calc_indexable(total_m, t)
            extra = f"인써트 {u}개, 홀더 {h}개"

        # --- 탑솔리드 ---
        elif t["type"] == "탑솔리드 인덱서블":
            cost, u, h = calc_topsolid(total_m, t)
            extra = f"인써트 {u}개, 홀더 {h}개"

        # --- 솔리드 ---
        else:
            cost, u, life = calc_solid(total_m, t)
            extra = f"본체 {u}개 (수명 {life:.1f} m)"

        # 결과 계산
        mcost = cost / max(1e-9, total_m)
        hcost = cost / max(1, total_holes)

        rows.append({
            "공구명": t["name"] or "(이름없음)",
            "종류": t["type"],
            "총비용": cost,
            "m당비용": mcost,
            "홀당비용": hcost,
            "비고": extra
        })

    # 데이터프레임 생성
    df = pd.DataFrame(rows)

    # 절감률 계산 (비싼 공구 대비)
    df["절감률(%)"] = (1 - df["m당비용"] / df["m당비용"].max()) * 100

    # 표 출력
    table.dataframe(df, use_container_width=True)

    # 그래프 생성
    fig = px.bar(
        df,
        x="공구명",
        y="m당비용",
        color="종류",
        text=df["절감률(%)"].apply(lambda x: f"{x:.1f}%"),
        title="공구별 M당 비용 비교"
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="m당 비용 (원)", xaxis_title="공구명")

    chart.plotly_chart(fig, use_container_width=True)


# --------------------------------------
# QR 코드 생성 기능 (버튼 클릭 시)
# --------------------------------------
if qr_btn:
    try:
        # 내부 아이피 기반 URL 생성
        ip = socket.gethostbyname(socket.gethostname())
        url = f"http://{ip}:8501"

        # QR 생성
        img = qrcode.make(url)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        # 화면 표시
        qrbox.image(buf, width=200)
        qrbox.markdown(f"**URL:** {url}")

    except Exception as e:
        qrbox.error(f"QR 코드 생성 실패: {str(e)}")
