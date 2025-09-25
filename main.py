# app.py
import streamlit as st
import pandas as pd
import re

# === Логика анализа (встроенная) ===

OUTCOMES = ['2:0', '2:1', '1:2', '0:2']

def extract_matches(line):
    return re.findall(r'\d+-\([^)]+\)', line)

def parse_match_part(part):
    match = re.match(r'^(\d+)-\((.+)\)$', part.strip())
    if not match:
        return None, None
    num_str, outcome_str = match.groups()
    try:
        num = int(num_str)
        if 1 <= num <= 14:
            options = [o.strip() for o in outcome_str.split(',') if o.strip() in OUTCOMES]
            return num, options if options else None
        else:
            return None, None
    except:
        return None, None

def parse_odds(text):
    odds = {}
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or '\t' not in line:
            continue
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        if len(parts) < 3:
            continue
        try:
            match_num = int(parts[0])
            p1 = float(parts[1])
            p2 = float(parts[2])
            odds[match_num] = {'p1': p1, 'p2': p2}
        except:
            continue
    return odds

def analyze_expert_consensus(expert_text):
    match_analysis = {i: {'p1_votes': 0, 'p2_votes': 0, 'total_votes': 0,
                         'p1_confidence': 0, 'p2_confidence': 0} for i in range(1, 15)}
    lines = expert_text.strip().split('\n')
    total_experts = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = extract_matches(line)
        if not parts:
            continue
        total_experts += 1
        for part in parts:
            match_num, options = parse_match_part(part)
            if match_num is None or options is None:
                continue
            for outcome in options:
                if outcome in ['2:0', '2:1']:
                    match_analysis[match_num]['p1_votes'] += 1
                elif outcome in ['1:2', '0:2']:
                    match_analysis[match_num]['p2_votes'] += 1
                match_analysis[match_num]['total_votes'] += 1

    for match_num in range(1, 15):
        total = match_analysis[match_num]['total_votes']
        if total > 0:
            match_analysis[match_num]['p1_confidence'] = match_analysis[match_num]['p1_votes'] / total
            match_analysis[match_num]['p2_confidence'] = match_analysis[match_num]['p2_votes'] / total

    return match_analysis, total_experts

def calculate_value_bets(expert_analysis, odds_data, min_confidence, min_odds, max_odds):
    value_bets = []
    for match_num in range(1, 15):
        if match_num not in odds_data:
            continue
        analysis = expert_analysis[match_num]
        odds = odds_data[match_num]
        if analysis['total_votes'] < 5:
            continue

        implied_p1 = 1 / odds['p1']
        implied_p2 = 1 / odds['p2']
        margin = implied_p1 + implied_p2 - 1
        fair_p1 = implied_p1 / (1 + margin)
        fair_p2 = implied_p2 / (1 + margin)

        value_p1 = analysis['p1_confidence'] - fair_p1
        value_p2 = analysis['p2_confidence'] - fair_p2

        if analysis['p1_confidence'] >= min_confidence and value_p1 > 0:
            recommended_player = 'П1'
            confidence = analysis['p1_confidence']
            value = value_p1
            odds_value = odds['p1']
        elif analysis['p2_confidence'] >= min_confidence and value_p2 > 0:
            recommended_player = 'П2'
            confidence = analysis['p2_confidence']
            value = value_p2
            odds_value = odds['p2']
        else:
            continue

        if min_odds <= odds_value <= max_odds:
            value_bets.append({
                'match': match_num,
                'player': recommended_player,
                'confidence': confidence,
                'value': value,
                'odds': odds_value,
                'votes': f"{analysis['p1_votes'] if recommended_player == 'П1' else analysis['p2_votes']}/{analysis['total_votes']}",
                'expert_consensus': f"{analysis['p1_confidence']:.1%} vs {analysis['p2_confidence']:.1%}"
            })

    value_bets.sort(key=lambda x: x['value'], reverse=True)
    return value_bets[:6]

# === Streamlit UI ===

st.set_page_config(
    page_title="🎾 Tennis Analyzer — Метод Шина",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 Tennis Analyzer — Метод Шина (6 из 14)")
st.markdown("Поиск 6 уверенных прогнозов из 14 теннисных матчей")

# Настройки
st.sidebar.header("⚙️ Настройки анализа")
min_confidence = st.sidebar.slider("Минимальная уверенность", 0.5, 0.9, 0.65, 0.01)
min_odds = st.sidebar.slider("Минимальный коэффициент", 1.5, 2.5, 1.70, 0.01)
max_odds = st.sidebar.slider("Максимальный коэффициент", 2.5, 5.0, 3.50, 0.01)

# Ввод данных
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Прогнозы экспертов")
    st.caption("Формат: `1-(2:0); 2-(1:2,0:2); ...`")
    expert_input = st.text_area(
        "Вставьте прогнозы:",
        height=300,
        value="""1-(2:0)
2-(1:2,0:2)
3-(2:1)
4-(2:0,2:1)
5-(1:2)
6-(2:0)
7-(0:2)
8-(2:1,1:2)
9-(2:0)
10-(1:2,0:2)
11-(2:1)
12-(2:0)
13-(1:2)
14-(2:0,2:1)"""
    )

with col2:
    st.subheader("📈 Коэффициенты")
    st.caption("Формат: `1\\t1.65\\t2.24` (табуляция между числами)")
    odds_input = st.text_area(
        "Вставьте коэффициенты:",
        height=300,
        value="""1\t1.65\t2.24
2\t2.10\t1.75
3\t1.80\t2.00
4\t1.70\t2.10
5\t2.30\t1.60
6\t1.90\t1.90
7\t1.95\t1.85
8\t2.20\t1.65
9\t1.75\t2.05
10\t2.40\t1.55
11\t1.85\t1.95
12\t1.60\t2.30
13\t2.00\t1.80
14\t1.95\t1.85"""
    )

# Анализ
if st.button("🎯 Найти 6 лучших ставок", type="primary"):
    if not expert_input.strip():
        st.error("Пожалуйста, введите прогнозы экспертов!")
    else:
        expert_analysis, total_experts = analyze_expert_consensus(expert_input)
        odds_data = parse_odds(odds_input) if odds_input.strip() else {}
        value_bets = calculate_value_bets(
            expert_analysis, odds_data,
            min_confidence, min_odds, max_odds
        )

        st.subheader(f"Результаты анализа ({total_experts} экспертов)")

        if not value_bets:
            st.warning("❌ Не найдено подходящих ставок")
        else:
            for i, bet in enumerate(value_bets, 1):
                with st.expander(f"🎯 Ставка #{i} — Матч {bet['match']}"):
                    st.markdown(f"""
                    - **Рекомендуем**: {bet['player']}
                    - **Уверенность**: {bet['confidence']:.1%}
                    - **Коэффициент**: {bet['odds']}
                    - **Value**: {bet['value']:.3f}
                    - **Голоса**: {bet['votes']}
                    - **Консенсус**: {bet['expert_consensus']}
                    """)

            avg_conf = sum(b['confidence'] for b in value_bets) / len(value_bets)
            st.success(f"Найдено **{len(value_bets)}** уверенных прогнозов. Средняя уверенность: **{avg_conf:.1%}**")

        # Детальная таблица
        st.subheader("📊 Детальный анализ всех матчей")
        table_data = []
        for match_num in range(1, 15):
            analysis = expert_analysis[match_num]
            if match_num in odds_data:
                odds = odds_data[match_num]
                odds_p1 = f"{odds['p1']:.2f}"
                odds_p2 = f"{odds['p2']:.2f}"
                is_recommended = any(b['match'] == match_num for b in value_bets)
                status = "✅ Рекомендуем" if is_recommended else "❌ Не рекомендован"
            else:
                odds_p1 = "-"
                odds_p2 = "-"
                status = "⚠️ Нет коэффициентов"

            table_data.append({
                "Матч": match_num,
                "Голоса П1": analysis['p1_votes'],
                "Голоса П2": analysis['p2_votes'],
                "Всего": analysis['total_votes'],
                "Уверенность П1": f"{analysis['p1_confidence']:.1%}",
                "Уверенность П2": f"{analysis['p2_confidence']:.1%}",
                "Кэф П1": odds_p1,
                "Кэф П2": odds_p2,
                "Статус": status
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
