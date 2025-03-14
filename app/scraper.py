import bs4
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models import Item
from app.settings import get_logger
from app.utils import convert_to_utc, get_current_date, get_random_user_agent

logger = get_logger('scraper')


class Scraper:
    """Web scraper for veri.bet that extracts betting odds information.

    This class handles fetching, parsing, and structuring betting data from veri.bet.
    It processes multiple sports and bet types, organizing them into structured Item objects.

    Attributes:
        user_agent (str): Random user agent string for HTTP requests
        index_url (str): URL template for fetching betting data by date
        session (requests.Session): HTTP session with retry configuration
        current_date (str): Current date formatted as MM-DD-YYYY
    """

    user_agent = get_random_user_agent()
    index_url = 'https://veri.bet/x-ajax-oddspicks?sDate={date}&showAll=yes'

    def __init__(self):
        """Initialize the scraper with a configured session and current date."""
        logger.debug('Initializing scraper')
        self.session = self._get_requests_session()
        self._configure_retry(status_to_force=[429, *range(500, 600)])
        self.current_date = get_current_date()
        logger.info(f'Scraper initialized with date: {self.current_date}')

    def start(self):
        """Start the scraping process and return structured betting data.

        Returns:
            list[Item]: List of betting items with all extracted data
        """
        logger.info('Starting scraping process')
        items = []
        grouped_data = self._fetch_and_group_data()

        logger.debug(f'Processing data for {len(grouped_data)} sport leagues')
        for sport_league, rows in grouped_data.items():
            logger.debug(f'Processing {len(rows)} rows for {sport_league}')
            sport_items = self._process_sport_league_rows(sport_league, rows)
            items.extend(sport_items)

        logger.info(f'Scraping completed, {len(items)} items extracted')
        return items

    def _fetch_and_group_data(self):
        """Fetch betting data from the website and group it by sport/league.

        Returns:
            dict: Data grouped by sport/league with corresponding HTML rows
        """
        logger.debug(f'Fetching data from: {self.index_url.format(date=self.current_date)}')
        response = self.session.get(self.index_url.format(date=self.current_date))

        if response.status_code != 200:
            logger.warning(f'Received non-200 status code: {response.status_code}')

        soup = self._get_soup(response)
        main_table = soup.find('table', id='odds-picks')

        if not main_table:
            logger.warning('Main table not found in the response')
            return {}

        rows_first_level = main_table.find_all('tr', recursive=False)
        logger.debug(f'Found {len(rows_first_level)} first-level rows')
        grouped_data = self._get_grouped_data(rows_first_level)
        logger.debug(f'Data grouped into {len(grouped_data)} categories')
        return grouped_data

    def _process_sport_league_rows(
        self, sport_league: str, rows: list[bs4.element.Tag]
    ) -> list[Item]:
        """Process all rows for a specific sport/league.

        Args:
            sport_league (str): Name of the sport or league
            rows (list[bs4.element.Tag]): List of HTML rows to process

        Returns:
            list[Item]: Betting items extracted from the rows
        """
        logger.debug(f'Processing rows for sport/league: {sport_league}')
        items = []
        for row in rows:
            row_items = self._process_game_divs(sport_league, row)
            items.extend(row_items)
        logger.debug(f'Processed {len(items)} items for {sport_league}')
        return items

    def _process_game_divs(self, sport_league: str, row: bs4.element.Tag) -> list[Item]:
        """Process game divisions within a row.

        Args:
            sport_league (str): Name of the sport or league
            row (bs4.element.Tag): HTML row containing game divisions

        Returns:
            list[Item]: Betting items for all games in the row
        """
        items = []
        div_games = row.find_all('div', class_='col col-md')
        logger.debug(f'Found {len(div_games)} game divisions to process')

        for div_game in div_games:
            game_items = self._process_single_game(div_game, sport_league)
            items.extend(game_items)
        return items

    def _process_single_game(self, div_game: bs4.element.Tag, sport_league: str) -> list[Item]:
        """Process a single game to extract all betting options.

        Extracts game information and processes odds for both teams.
        For soccer, also processes the draw option.

        Args:
            div_game (bs4.element.Tag): HTML division containing a game
            sport_league (str): Name of the sport or league

        Returns:
            list[Item]: All betting items for this game
        """
        items = []
        table_game = div_game.find('table')
        if not table_game:
            logger.warning(f'No table found in game division for {sport_league}')
            return items

        table_game_rows = table_game.find_all('tr', recursive=False)
        if len(table_game_rows) < 3:
            logger.warning(
                f'Insufficient rows in game table for {sport_league}: {len(table_game_rows)}'
            )
            return items

        game_info = self._extract_game_info(table_game_rows)
        logger.debug(
            f'Processing game: {game_info["team1"]} vs {game_info["team2"]} at {game_info["time"]}'
        )

        # Process regular team odds (for both teams)
        for table_game_row in table_game_rows[1:3]:
            team_items = self._process_team_odds(
                table_game_row,
                game_info['period'],
                game_info['time'],
                game_info['team1'],
                game_info['team2'],
                sport_league,
            )
            items.extend(team_items)

        # Process special case for soccer
        if sport_league == 'SOCCER':
            draw_item = self._process_soccer_draw_odds(
                table_game_rows[3],
                game_info['period'],
                game_info['time'],
                game_info['team1'],
                game_info['team2'],
                sport_league,
            )
            items.append(draw_item)

        return items

    def _extract_game_info(self, table_game_rows: list[bs4.element.Tag]) -> dict:
        """Extract basic game information from table rows.

        Args:
            table_game_rows (list[bs4.element.Tag]): List of table rows with game info

        Returns:
            dict: Dictionary containing period, team names, and game time
        """
        period = self._clean_text(table_game_rows[0].find('span', class_='text-muted').text)
        team1 = table_game_rows[1].find('span', class_='text-muted').text.strip()
        team2 = table_game_rows[2].find('span', class_='text-muted').text.strip()
        time_raw = (
            table_game_rows[3]
            .find('span', class_='badge badge-light text-wrap text-left')
            .text.strip()
        )
        time = self._clean_text(time_raw)

        if time not in {'FINAL', 'IN PROGRESS'}:
            time = convert_to_utc(time)

        return {'period': period, 'team1': team1, 'team2': team2, 'time': time}

    def _process_team_odds(
        self,
        table_game_row: bs4.element.Tag,
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str,
    ) -> list[Item]:
        """Process all betting odds for a team.

        Extracts moneyline, spread, and over/under odds for a single team.

        Args:
            table_game_row (bs4.element.Tag): HTML row with team odds
            period (str): Game period identifier
            time (str): Game time or status in UTC
            team1 (str): Name of team 1
            team2 (str): Name of team 2
            sport_league (str): Sport or league name

        Returns:
            list[Item]: Three betting items (moneyline, spread, over/under)
        """
        items = []
        tds = table_game_row.find_all('td', recursive=False)

        moneyline_item = self._get_moneyline_item(tds, period, time, team1, team2, sport_league)
        items.append(moneyline_item)

        spread_item = self._get_spread_item(tds, period, time, team1, team2, sport_league)
        items.append(spread_item)

        under_over_item = self._get_under_over_item(tds, period, time, team1, team2, sport_league)
        items.append(under_over_item)

        return items

    def _process_soccer_draw_odds(
        self,
        table_game_row: bs4.element.Tag,
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str,
    ) -> Item:
        """Process soccer draw odds.

        Special case for soccer games where a draw is a possible outcome.

        Args:
            table_game_row (bs4.element.Tag): HTML row with draw odds
            period (str): Game period identifier
            time (str): Game time or status in UTC
            team1 (str): Name of team 1
            team2 (str): Name of team 2
            sport_league (str): Should be 'SOCCER'

        Returns:
            Item: Draw betting item
        """
        logger.debug(f'Processing soccer draw odds for {team1} vs {team2}')
        tds = table_game_row.find_all('td', recursive=False)
        return self._get_soccer_draw_moneyline_item(tds, period, time, team1, team2, sport_league)

    @staticmethod
    def _get_soccer_draw_moneyline_item(
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str,
    ) -> Item:
        """Extract soccer draw moneyline odds.

        Args:
            table_game_row_tds (list[bs4.element.Tag]): HTML table cells with odds
            period (str): Game period identifier
            time (str): Game time or status in UTC
            team1 (str): Name of team 1
            team2 (str): Name of team 2
            sport_league (str): Should be 'SOCCER'

        Returns:
            Item: Draw moneyline betting item
        """
        side = team = 'draw'
        line_type = 'moneyline'
        spread = 0
        money_line_column = table_game_row_tds[1]
        draw_text = (
            money_line_column.find('span', class_='text-muted')
            .text.strip()
            .replace('\r\n', ' ')
            .replace('\t', '')
        )
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
            pitcher='',
        )

    @staticmethod
    def _get_moneyline_item(
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str,
    ) -> Item:
        """Extract moneyline odds for a team.

        Args:
            table_game_row_tds (list[bs4.element.Tag]): HTML table cells with odds
            period (str): Game period identifier
            time (str): Game time or status in UTC
            team1 (str): Name of team 1
            team2 (str): Name of team 2
            sport_league (str): Sport or league name

        Returns:
            Item: Moneyline betting item
        """
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
            pitcher='',
        )

    @staticmethod
    def _get_spread_item(
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str,
    ) -> Item:
        """Extract spread betting odds for a team.

        Args:
            table_game_row_tds (list[bs4.element.Tag]): HTML table cells with odds
            period (str): Game period identifier
            time (str): Game time or status in UTC
            team1 (str): Name of team 1
            team2 (str): Name of team 2
            sport_league (str): Sport or league name

        Returns:
            Item: Spread betting item
        """
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
            pitcher='',
        )

    @staticmethod
    def _get_under_over_item(
        table_game_row_tds: list[bs4.element.Tag],
        period: str,
        time: str,
        team1: str,
        team2: str,
        sport_league: str,
    ) -> Item:
        """Extract over/under (totals) betting odds for a team.

        Args:
            table_game_row_tds (list[bs4.element.Tag]): HTML table cells with odds
            period (str): Game period identifier
            time (str): Game time or status in UTC
            team1 (str): Name of team 1
            team2 (str): Name of team 2
            sport_league (str): Sport or league name

        Returns:
            Item: Over/under betting item
        """
        line_type = 'over/under'
        over_under_column = table_game_row_tds[3]
        over_under_full_text = (
            over_under_column.find('span', class_='text-muted')
            .text.strip()
            .replace('\r\n', ' ')
            .replace('\t', '')
        )

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
            pitcher='',
        )

    @staticmethod
    def _get_grouped_data(rows: list[bs4.element.Tag]) -> dict:
        """Group HTML rows by sport/league.

        Args:
            rows (list[bs4.element.Tag]): List of HTML rows to group

        Returns:
            dict: Dictionary with sport/league names as keys and rows as values
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

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text by removing whitespace and special characters.

        Args:
            text (str): Text to clean

        Returns:
            str: Cleaned text
        """
        return text.strip().replace('\r', '').replace('\n', '').replace('\t', '')

    def _get_requests_session(self) -> requests.Session:
        """Create and configure a requests session with custom user agent.

        Returns:
            requests.Session: Configured session
        """
        logger.debug('Creating requests session with user agent')
        session = requests.Session()
        session.headers.update({'User-Agent': self.user_agent})
        return session

    @staticmethod
    def _get_soup(response: requests.Response) -> bs4.BeautifulSoup:
        """Convert HTTP response to BeautifulSoup object.

        Args:
            response (requests.Response): HTTP response

        Returns:
            bs4.BeautifulSoup: Parsed HTML
        """
        return bs4.BeautifulSoup(response.text, 'html.parser')

    def _configure_retry(self, status_to_force: list = [], total_retries: int = 3):
        """Configure automatic retry for HTTP requests.

        Sets up retry mechanism for handling transient HTTP errors.

        Args:
            status_to_force (list): HTTP status codes that should trigger a retry
            total_retries (int): Maximum number of retry attempts
        """
        logger.debug(f'Configuring retry strategy with {total_retries} retries')
        retry_strategy = Retry(
            total=total_retries,
            backoff_factor=2,
            status_forcelist=status_to_force,
            allowed_methods=['HEAD', 'GET', 'OPTIONS', 'POST'],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
