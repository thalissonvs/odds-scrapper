from app.scraper import Scraper
import time
from dataclasses import asdict

def main():
    scraper = Scraper()
    previous_items = []
    
    while True:
        current_items = scraper.start()
        
        # Find new and changed items
        new_or_changed = []
        for current in current_items:
            is_new_or_changed = True
            for prev in previous_items:
                if current == prev:
                    is_new_or_changed = False
                    break
            if is_new_or_changed:
                new_or_changed.append(current)


        removed_items = []
        for prev in previous_items:
            if prev not in current_items:
                removed_items.append(prev)
        
        if not new_or_changed and not removed_items:
            print("NO CHANGES")
        else:
            # Print new or changed items
            if new_or_changed:
                for item in new_or_changed:
                    print(asdict(item))
            
            if removed_items:
                print("REMOVED ITEMS")
                for item in removed_items:
                    print(asdict(item))
        
        previous_items = current_items.copy()
        time.sleep(10)


if __name__ == '__main__':
    main()