from dataclasses import dataclass

@dataclass
class Item:
    sport_league: str = ''     # sport as we classify it, e.g. baseball, basketball, football
    event_date_utc: str = ''   # date of the event, in UTC, ISO format
    team1: str = ''            # team 1 name
    team2: str = ''            # team 2 name
    pitcher: str = ''          # optional, pitcher for baseball
    period: str = ''           # full time, 1st half, 1st quarter and so on
    line_type: str = ''        # whatever site reports as line type, e.g. moneyline, spread, over/under
    price: str = ''            # price site reports, e.g. '-133' or '+105'
    side: str = ''             # side of the bet for over/under, e.g. 'over', 'under'
    team: str = ''             # team name, for over/under bets this will be either team name or total
    spread: float = 0.0        # for handicap and over/under bets, e.g. -1.5, +2.5