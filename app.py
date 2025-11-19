import streamlit as st
import math

# ---------------------------------------------------
# 기본 Streamlit 설정
# ---------------------------------------------------
st.set_page_config(page_title="KDM 절감 시뮬레이터", layout="wide")
st.title("🛠️ KING DRILL MINI 적용 시 절감효과 시뮬레이터")

# ---------------------------------------------------
# KDM 고정 기준값
# ---------------------------------------------------
KDM = {
    "name": "King Drill Mini",
    "corner_life_m": 17,
    "corners": 2,
    "insert_price": 9000,
    "holder_price": 60000,
    "holder_ratio": 15,
    "change_time": 30
}

# ---------------------------------------------------
# 유틸 함수들
# ---------------------------------------------------
def safe(v, d=0):
    try:
        return float(v)
    except:
        return d

def nceil(v):
    return int(math.ceil(v))

# ---------------------------------------------------
# 좌측 입력 UI
# ---------------------------------------------------
st.sidebar.header("🔧 현재 사용하는 공구 조건 입력")

basis = st.sidebar.radio("기준 선택", ["거리(m)", "홀수(개)"], horizontal=True)
ap = st.sidebar.number_input("절입깊이 ap (m/홀)", value=0.03, min_value=0.001)

if basis == "거리(m)":
    total_m = st.sidebar.number_input("총 가공거리(m)", value=30.0)
    total_holes = nceil(total_m / ap)
else:
    total_holes = st.sidebar.number_input("총 홀수(개)", value=1000)
    total_m = total_holes * ap

st.sidebar.caption(f"→ 환산: **{total_m:.2f} m / {total_holes:,} 홀**")

st.sidebar.markdown("---")

st.sidebar.subheader("📌 비교 공구 입력")

price = st.sidebar.number_input("공구 가격(원)", value=50000, step=1000)
life_m = st.sidebar.number_input("공구 1본 수명(m)", value=10.0)
change_time_user = st.sidebar.number_input("공구 교체 시간(초)", value=30)

re_cnt = st.sidebar.number_input("재연마 횟수(회)", value=0, step=1)
re_price = st.sidebar.number_input("재연마 가격(원)", value=0, step=100)
re_ratio = st.sidebar.number_input("재연마 수명 회복률(배)", value=1.0, step=0.1)

# ---------------------------------------------------
# 계산: KDM 기준
# ---------------------------------------------------
def calc_kdm(total_m):
    insert_life_total = KDM["corner_life_m"] * KDM["corners"]
    needed_inserts = nceil(total_m / insert_life_total)
    needed_holders = nceil(needed_inserts / KDM["holder_ratio"])

    total_cost = needed_inserts * KDM["insert_price"] + needed_holders * KDM["holder_price"]
    change_cnt = needed_inserts
    change_time = change_cnt * KDM["change_time"]

    return {
        "cost": total_cost,
        "change_cnt": change_cnt,
        "change_time": change_time
    }

# ---------------------------------------------------
# 계산: 사용자 공구
# ---------------------------------------------------
def calc_user_tool(total_m):
    base = safe(life_m)
    total_life = base + re_cnt * (base * re_ratio)

    needed = nceil(total_m / total_life)
    total_cost = needed * (price + re_cnt * re_price)
    change_cnt = needed
    change_time = needed * change_time_user

    return {
        "cost": total_cost,
        "change_cnt": change_cnt,
        "change_time": change_time
    }

kdm = calc_kdm(total_m)
user = calc_user_tool(total_m)

# ---------------------------------------------------
# 절감 효과 계산
# ---------------------------------------------------
cost_save = user["cost"] - kdm["cost"]
time_save = (user["change_time"] - kdm["change_time"]) / 60  # 분
time_save_hr = time_save / 60  # 시간

saving_rate = (1 - kdm["cost"] / user["cost"]) * 100 if user["cost"] != 0 else 0
saving_rate = max(0, saving_rate)

# 연간 환산 (작업일수 300일 기준)
annual_time_save_hr = time_save_hr * 300
annual_money_save = cost_save

# 추가 생산 가능 부품 수 (총절약된 시간 / 1부품 생산 시간 기준)
# * 일단 1부품 생산 시간이 1분이라고 가정 — 나중에 변경 가능
extra_parts = max(0, int((annual_time_save_hr * 60) / 1))
extra_value = extra_parts * 1  # 향후 단가 입력 가능

# ===================================================
# CSS (카드 UI + 원형 게이지)
# ===================================================
st.markdown("""
<style>

.card {
    padding: 20px;
    border-radius: 12px;
    border: 2px solid #d0d0d0;
    background-color: #ffffff;
}

.circle-wrap {
    margin: 0 auto;
    width: 120px;
    height: 120px;
    background: #e6e2e7;
    border-radius: 50%;
    position: relative;
}

.circle-wrap .circle .mask,
.circle-wrap .circle .fill {
    width: 120px;
    height: 120px;
    position: absolute;
    border-radius: 50%;
}

.circle-wrap .circle .mask {
    clip: rect(0px, 120px, 120px, 60px);
}

.circle-wrap .circle .mask .fill {
    clip: rect(0px, 60px, 120px, 0px);
    background-color: #3b8ed9;
}

.circle-wrap .inside-circle {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: white;
    line-height: 90px;
    text-align: center;
    margin-top: 15px;
    margin-left: 15px;
    position: absolute;
    font-size: 20px;
    font-weight: bold;
    color: #3b8ed9;
}

.icon-line {
    display: flex;
    align-items: center;
    font-size: 18px;
    padding: 6px 0px;
}

.icon-line img {
    width: 28px;
    margin-right: 10px;
}

.value-blue {
    color: #3b8ed9;
    font-weight: bold;
    font-size: 20px;
}

</style>
""", unsafe_allow_html=True)

# ===================================================
# 중앙 결과 카드 UI
# ===================================================
st.markdown("## 📌 KDM 적용 시 절감 효과")

col1, col2 = st.columns([1.2, 2])

# -----------------------------
# 좌측 카드 UI
# -----------------------------
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # 원형 게이지
    st.markdown(f"""
    <div class="circle-wrap">
        <div class="circle">
            <div class="mask full">
                <div class="fill" style="transform: rotate({saving_rate * 1.8}deg);"></div>
            </div>
        </div>
        <div class="inside-circle">{saving_rate:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

    # 공구 이미지
    st.image("https://via.placeholder.com/120.png?text=KDM", width=120)

    # 절감값 텍스트
    st.markdown(f"""
    <div class="icon-line">
        <img src="https://img.icons8.com/ios-filled/50/clock.png">
        연간 총 절약 시간: <span class="value-blue">{annual_time_save_hr:.1f} 시간</span>
    </div>

    <div class="icon-line">
        <img src="https://img.icons8.com/ios-filled/50/wallet.png">
        연간 절약 금액: <span class="value-blue">{annual_money_save:,} 원</span>
    </div>

    <div class="icon-line">
        <img src="https://img.icons8.com/ios-filled/50/factory.png">
        연간 추가 생산 가능 부품 수: <span class="value-blue">{extra_parts} 개</span>
    </div>

    <div class="icon-line">
        <img src="https://img.icons8.com/ios-filled/50/money-bag.png">
        연간 추가 생산 가치: <span class="value-blue">{extra_value:,} 원</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# 우측 — 디버그용 값 표시
# -----------------------------
with col2:
    st.subheader("🔍 비교 상세 내역")
    st.write(f"**사용자 공구 총 비용:** {user['cost']:,} 원")
    st.write(f"**KDM 총 비용:** {kdm['cost']:,} 원")
    st.write(f"**절약 금액:** {annual_money_save:,} 원")
    st.write(f"**절약 시간:** {annual_time_save_hr:.2f} 시간/년")

