import requests
import bs4
from loguru import logger

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

from app.utils import get_random_user_agent, convert_to_utc
from app.models import Item


class Scraper:
    
    user_agent = get_random_user_agent()
    index_url = 'https://veri.bet/x-ajax-oddspicks?sDate={date}&showAll=yes'

    def __init__(self):
        self.session = self._get_requests_session()
        self._configure_retry(
            status_to_force=[429, *range(500, 600)]
        )
        self.current_date = self._get_current_date()
    
    def start(self):
        response = self.session.get(
            self.index_url.format(date=self.current_date)
        )
        soup = self._get_soup(response)
        main_table = soup.find('table', id='odds-picks')
        rows_first_level = main_table.find_all('tr', recursive=False)
        grouped_data = self._get_grouped_data(rows_first_level)
        
        items = []
        for sport_league, rows in grouped_data.items():
            for row in rows:
                div_games = row.find_all('div', class_='col col-md')
                
                for div_game in div_games:
                    table_game = div_game.find('table')
                    table_game_rows = table_game.find_all('tr', recursive=False)

                    period = table_game_rows[0].find('span', class_='text-muted').text.strip().replace('\r', '').replace('\n', '').replace('\t', '')
                    team1 = table_game_rows[1].find('span', class_='text-muted').text.strip()
                    team2 = table_game_rows[2].find('span', class_='text-muted').text.strip()
                    time = table_game_rows[3].find('span', class_='badge badge-light text-wrap text-left').text.strip().replace('\r', '').replace('\n', '').replace('\t', '')
                    time = convert_to_utc(time) if time not in ['FINAL', 'IN PROGRESS'] else time
                    # the items above will be the same for all the current game
                    # below will be the different items for each period
                    for table_game_row in table_game_rows[1:3]:
                        tds = table_game_row.find_all('td', recursive=False)
                        
                        moneyline_item = self._get_moneyline_item(tds, period, time, team1, team2, sport_league)
                        items.append(moneyline_item)

                        spread_item = self._get_spread_item(tds, period, time, team1, team2, sport_league)
                        items.append(spread_item)

                        under_over_item = self._get_under_over_item(tds, period, time, team1, team2, sport_league)
                        items.append(under_over_item)

                    if sport_league == 'SOCCER':
                        table_game_row = table_game_rows[3]
                        tds = table_game_row.find_all('td', recursive=False)
                        draw_moneyline_item = self._get_soccer_draw_moneyline_item(tds, period, time, team1, team2, sport_league)
                        items.append(draw_moneyline_item)

        return items

    def _get_items(self, rows: list[bs4.element.Tag]) -> list[Item]:
        # first for loop
        ...


    def _get_soccer_draw_moneyline_item(
        self,
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str
    ) -> Item:
        side = team = 'draw'
        line_type = 'moneyline'
        spread = 0
        money_line_column = table_game_row_tds[1]
        draw_text = money_line_column.find('span', class_='text-muted').text.strip().replace('\r\n', ' ').replace('\t', '')
        price = draw_text.split(' ')[1]
        return Item(
            side=side,
            team=team,
            line_type=line_type,
            price=price,
            spread=spread,
            sport_league=sport_league,
            event_date_utc=time,
            team1=team1,
            team2=team2,
            period=period,  
            pitcher=''
        )

    def _get_moneyline_item(
        self,
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str
    ) -> Item:
        side = team = table_game_row_tds[0].find('span', class_='text-muted').text.strip()
        line_type = 'moneyline'
        money_line_column = table_game_row_tds[1]
        price = money_line_column.find('span', class_='text-muted').text.strip()
        spread = 0
        
        return Item(
            side=side,
            team=team,
            line_type=line_type,
            price=price,
            spread=spread,
            sport_league=sport_league,
            event_date_utc=time,
            team1=team1,
            team2=team2,
            period=period,
            pitcher=''
        )

    
    def _get_spread_item(
        self,
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str
    ) -> Item:
        side = team = table_game_row_tds[0].find('span', class_='text-muted').text.strip()
        line_type = 'spread'
        spread_column = table_game_row_tds[2]
        spread_full_text = spread_column.find('span', class_='text-muted').text.strip()
        
        if spread_full_text == 'N/A':
            price = spread = 'N/A'
        else:
            price = spread_full_text.split('(')[1].split(')')[0].strip()
            spread = spread_full_text.split('(')[0].strip()

        return Item(
            side=side,
            team=team,
            line_type=line_type,
            price=price,
            spread=spread,
            sport_league=sport_league,
            event_date_utc=time,
            team1=team1,
            team2=team2,
            period=period,
            pitcher=''
        )

    def _get_under_over_item(
        self,
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str
    ) -> Item:
        line_type = 'over/under'
        over_under_column = table_game_row_tds[3]
        over_under_full_text = over_under_column.find('span', class_='text-muted').text.strip().replace('\r\n', ' ').replace('\t', '') 
        
        if over_under_full_text == 'N/A':
            price = spread = 'N/A'
        else:
            price = over_under_full_text.split('(')[1].split(')')[0].strip()
            spread = over_under_full_text.split('(')[0].strip().split(' ')[1].strip()

        team = 'total'
        side = over_under_full_text.split(' ')[0].strip()
        side = 'over' if side == 'O' else 'under'

        return Item(
            side=side,
            team=team,
            line_type=line_type,
            price=price,
            spread=spread,
            sport_league=sport_league,
            event_date_utc=time,
            team1=team1,
            team2=team2,
            period=period,
            pitcher=''
        )
    
    
    def _get_grouped_data(self, rows: list[bs4.element.Tag]) -> dict:
        """
        Group rows by sport league
        """
        grouped_data = {}
        current_group = None
        
        for row in rows:
            sport_league = row.find('h2')
            if sport_league:
                current_group = sport_league.text.strip()
                grouped_data[current_group] = []
                continue
            grouped_data[current_group].append(row)
        
        return grouped_data

    def _get_current_date(self) -> str:
        return datetime.now().strftime('%m-%d-%Y')
    
    def _get_requests_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.user_agent
        })
        return session
    
    def _get_soup(self, response: requests.Response) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(response.text, 'html.parser')
    
    def _configure_retry(self, status_to_force: list = [], total_retries: int = 3):
        logger.debug('_configure_retry')
        retry_strategy = Retry(
            total=total_retries,
            backoff_factor=2,
            status_forcelist=status_to_force,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)