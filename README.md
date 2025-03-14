# Odds Scraper

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![BeautifulSoup4](https://img.shields.io/badge/BeautifulSoup4-4.13.3-orange.svg)
![Requests](https://img.shields.io/badge/Requests-2.32.3-red.svg)
![Loguru](https://img.shields.io/badge/Loguru-0.7.3-purple.svg)

A web scraper application for tracking and monitoring betting odds from veri.bet in real-time.

## Overview

Odds Scraper is a tool designed to extract, process, and monitor betting odds for various sports from veri.bet. The application continuously scrapes the website at regular intervals, processes the data, and detects changes in odds over time.

## Technologies Used

- **Python 3.12**: Core programming language
- **BeautifulSoup4**: HTML parsing and data extraction
- **Requests**: HTTP request handling with retry capabilities
- **Loguru**: Advanced logging with structured output
- **Poetry**: Dependency management and packaging
- **Docker**: Containerization for easy deployment
- **UA-Generator**: User agent generation for web scraping

## Project Structure

```
odds-scraper/
├── app/                   # Main application package
│   ├── models.py          # Data models for betting items
│   ├── scraper.py         # Web scraper implementation
│   ├── settings.py        # Application settings and logging configuration
│   └── utils.py           # Utility functions (time conversion, etc.)
├── logs/                  # Log output directory
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose configuration
├── main.py                # Application entry point
├── poetry.lock            # Poetry lock file (dependencies)
├── pyproject.toml         # Project configuration and dependencies
└── README.md              # This file
```

## Installation and Usage

There are two methods to install and run the Odds Scraper application:

### Method 1: Using Docker (Recommended)

The recommended way to run Odds Scraper is using Docker, which handles all dependencies and environment setup automatically.

#### Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

#### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/thalissonvs/odds-scraper.git
   cd odds-scraper
   ```

2. Build and start the application:
   ```bash
   docker-compose up -d
   ```

3. View the logs:
   ```bash
   docker-compose logs -f
   ```

4. Stop the application:
   ```bash
   docker-compose down
   ```

### Method 2: Manual Installation

If you prefer to run the application directly on your system, follow these steps:

#### Prerequisites

- Python 3.12 installed
- Poetry installed (see [Poetry Installation Guide](https://python-poetry.org/docs/#installation))

#### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/odds-scraper.git
   cd odds-scraper
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

3. Run the application:
   ```bash
   poetry run python main.py
   ```

   Alternatively, activate the Poetry shell and run the application:
   ```bash
   poetry shell
   python main.py
   ```

## Configuration

The application's configuration is managed in the `app/settings.py` file. Key settings include:

- `SCRAPER_INTERVAL_SECONDS`: Time between scraping cycles (default: 10 seconds)
- `USER_AGENT_ROTATION`: Whether to rotate user agents for each request
- Logging configuration (log levels, formats, rotation, etc.)

## Logging

Odds Scraper uses Loguru for advanced logging:

- Console output includes color-coded log levels for easy monitoring
- Log files are stored in the `logs` directory
- Log files rotate automatically when they reach 10 MB
- Log retention is set to 1 month
- Logs are compressed in ZIP format

## Development

For development:

1. Install development dependencies:
   ```bash
   poetry install --with dev
   ```

2. Run linting and formatting:
   ```bash
   poetry run task lint
   poetry run task format
   ```

## Acknowledgements

- [veri.bet](https://veri.bet) - Source of betting odds data (used for educational purposes)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing library
- [Requests](https://requests.readthedocs.io/) - HTTP library
- [Loguru](https://github.com/Delgan/loguru) - Logging library
- [Poetry](https://python-poetry.org/) - Dependency management 