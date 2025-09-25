# app.py
import streamlit as st
import pandas as pd
from analyzer import TennisAnalyzerCore

# Настройки страницы
st.set_page_config(
    page_title="🎾 Tennis Analyzer - Метод Шина",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 Tennis Analyzer — Метод Шина (6 из 14)")
st.markdown("Поиск 6 уверенных прогнозов из 14 теннисных матчей")

# Настройки анализа
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

# Кнопка анализа
if st.button("🎯 Найти 6 лучших ставок", type="primary"):
    if not expert_input.strip():
        st.error("Пожалуйста, введите прогнозы экспертов!")
    else:
        # Запуск анализа
        analyzer = TennisAnalyzerCore(
            min_confidence=min_confidence,
            min_odds=min_odds,
            max_odds=max_odds
        )
        
        expert_analysis, total_experts = analyzer.analyze_expert_consensus(expert_input)
        odds_data = analyzer.parse_odds(odds_input) if odds_input.strip() else {}
        value_bets = analyzer.calculate_value_bets(expert_analysis, odds_data)

        # Отображение результатов
        st.subheader(f"Результаты анализа ({total_experts} экспертов)")

        if not value_bets:
            st.warning("❌ Не найдено подходящих ставок")
        else:
            # Рекомендуемые ставки
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

            # Статистика
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