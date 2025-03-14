from dataclasses import dataclass


@dataclass
class Item:
    sport_league: str = ''
    event_date_utc: str = ''
    team1: str = ''
    team2: str = ''
    pitcher: str = ''
    period: str = ''
    line_type: str = ''
    price: str = ''
    side: str = ''
    team: str = ''
    spread: float = 0.0
