import time
from dataclasses import asdict

from app.scraper import Scraper
from app.settings import get_logger

# Get logger for main module
logger = get_logger('main')


def main():
    """
    Main entry point for the odds scraper application.

    This function initializes the scraper and runs it in a continuous loop,
    comparing current data with previous data to detect and report changes.
    """
    logger.info('Initializing odds scraper application')
    scraper = Scraper()
    previous_items = []

    while True:
        logger.info('Starting new scraping cycle')
        logger.debug(f'Previous cycle had {len(previous_items)} items')

        current_items = scraper.start()
        logger.debug(f'Current cycle found {len(current_items)} items')

        new_or_changed = find_new_or_changed_items(current_items, previous_items)
        removed_items = find_removed_items(current_items, previous_items)

        logger.info(
            f'Found {len(new_or_changed)} new/changed items and {len(removed_items)} removed items'
        )
        report_changes(new_or_changed, removed_items)

        previous_items = current_items.copy()
        logger.debug('Waiting for next cycle')
        time.sleep(10)


def find_new_or_changed_items(current_items, previous_items):
    """Find items that are new or have changed compared to previous items.

    Args:
        current_items (list): Current list of scraped items
        previous_items (list): Previous list of scraped items

    Returns:
        list: Items that are new or have changed
    """
    logger.debug('Looking for new or changed items')
    new_or_changed = []
    for current in current_items:
        is_new_or_changed = True
        for prev in previous_items:
            if current == prev:
                is_new_or_changed = False
                break
        if is_new_or_changed:
            logger.debug(
                f'Found new/changed item: {current.team1} vs {current.team2} - {current.line_type}'
            )
            new_or_changed.append(current)
    return new_or_changed


def find_removed_items(current_items, previous_items):
    """Find items that were present before but are now removed.

    Args:
        current_items (list): Current list of scraped items
        previous_items (list): Previous list of scraped items

    Returns:
        list: Items that have been removed
    """
    logger.debug('Looking for removed items')
    removed_items = []
    for prev in previous_items:
        if prev not in current_items:
            logger.debug(f'Found removed item: {prev.team1} vs {prev.team2} - {prev.line_type}')
            removed_items.append(prev)
    return removed_items


def report_changes(new_or_changed, removed_items):
    """Report any changes found to the console.

    Args:
        new_or_changed (list): List of new or changed items
        removed_items (list): List of removed items
    """
    if not new_or_changed and not removed_items:
        logger.info('No changes detected in this cycle')
        logger.info('NO CHANGES')
    else:
        # Print new or changed items
        if new_or_changed:
            logger.info(f'Reporting {len(new_or_changed)} new or changed items')
            for item in new_or_changed:
                print(asdict(item))

        if removed_items:
            logger.info(f'Reporting {len(removed_items)} removed items')
            logger.info('REMOVED ITEMS')
            for item in removed_items:
                print(asdict(item))


if __name__ == '__main__':
    logger.info('Application startup')
    main()
