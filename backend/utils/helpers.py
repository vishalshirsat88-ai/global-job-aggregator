from datetime import datetime

def normalize_date(val):
    try:
        return datetime.fromisoformat(val.replace("Z","").replace(".000",""))
    except:
        return None

def parse_date(val):
    try:
        return datetime.fromisoformat(val.replace("Z","").replace(".000",""))
    except:
        return None

def skill_match(text, skill):
    if not text or not skill:
        return False
    return skill.lower() in text.lower()

def work_mode(text):
    t = (text or "").lower()
    if "remote" in t:
        return "Remote"
    if "hybrid" in t:
        return "Hybrid"
    return "On-site"

def excel_link(url):
    return f'=HYPERLINK("{url}","Apply")' if url else ""

def city_match(row_location, search_locations):
    if not row_location:
        return False
    row_loc = row_location.lower()
    return any(loc.lower() in row_loc for loc in search_locations)

