# analyzer.py
import re

class TennisAnalyzerCore:
    def __init__(self, min_confidence=0.65, min_odds=1.70, max_odds=3.50):
        self.OUTCOMES = ['2:0', '2:1', '1:2', '0:2']
        self.MIN_CONFIDENCE = min_confidence
        self.MIN_ODDS = min_odds
        self.MAX_ODDS = max_odds

    def extract_matches(self, line):
        return re.findall(r'\d+-\([^)]+\)', line)

    def parse_match_part(self, part):
        match = re.match(r'^(\d+)-\((.+)\)$', part.strip())
        if not match:
            return None, None
        num_str, outcome_str = match.groups()
        try:
            num = int(num_str)
            if 1 <= num <= 14:
                options = [o.strip() for o in outcome_str.split(',') if o.strip() in self.OUTCOMES]
                return num, options if options else None
            else:
                return None, None
        except:
            return None, None

    def parse_odds(self, text):
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

    def analyze_expert_consensus(self, expert_text):
        match_analysis = {i: {'p1_votes': 0, 'p2_votes': 0, 'total_votes': 0,
                             'p1_confidence': 0, 'p2_confidence': 0} for i in range(1, 15)}
        lines = expert_text.strip().split('\n')
        total_experts = 0

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = self.extract_matches(line)
            if not parts:
                continue
            total_experts += 1
            for part in parts:
                match_num, options = self.parse_match_part(part)
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

    def calculate_value_bets(self, expert_analysis, odds_data):
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

            if analysis['p1_confidence'] >= self.MIN_CONFIDENCE and value_p1 > 0:
                recommended_player = 'П1'
                confidence = analysis['p1_confidence']
                value = value_p1
                odds_value = odds['p1']
            elif analysis['p2_confidence'] >= self.MIN_CONFIDENCE and value_p2 > 0:
                recommended_player = 'П2'
                confidence = analysis['p2_confidence']
                value = value_p2
                odds_value = odds['p2']
            else:
                continue

            if self.MIN_ODDS <= odds_value <= self.MAX_ODDS:
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