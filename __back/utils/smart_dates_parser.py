from datetime import datetime, date
from typing import Optional
import re

def parse_date_from_str_to_str(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    if '.' not in date_str:
        return None
    
    parts = date_str.split('.')
    
    try:
        if len(parts) == 2:
            day = int(parts[0])
            month = int(parts[1])
            year = datetime.now().year
            
            return date(year, month, day).strftime('%d.%m.%Y')
            
        elif len(parts) == 3:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            if year < 100:
                year += 2000
            
            return date(year, month, day).strftime('%d.%m.%Y')
            
        else:
            return None
            
    except (ValueError, IndexError):
        return None