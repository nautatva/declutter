from datetime import datetime
from parsers.file_name_parser import parse_date_from_file_name
from parsers.exif_parser import extract_exif_date_taken
from pathlib import Path


def get_most_accurate_creation_date_from_file(file_path:str, quick=False, super_quick=False, ultra_quick=False) -> datetime:  
    # First check if file name has date
    dates = []
    if ultra_quick is True:
        super_quick = True
    if super_quick is True:
        quick = True


    file_date = None
    if ultra_quick is False:
        file_date = parse_date_from_file_name(file_path)
        # print("file_date", file_date)
        if file_date is not None:
            # Best case
            dates.append(file_date)
    
    run_exif = True
    # Always run extract exif if both quick and super quick are false
    # If quick is true, run only if file_date is None
    if quick is True and file_date is not None:
        run_exif = False

    # If super quick is true, never run
    if super_quick is True:
        run_exif = False


    if run_exif is True:
        # This quickly becomes heavy
        # Only computing exif date if date not found in file name
        exif_date = extract_exif_date_taken(file_path)
        if exif_date is not None:
            dates.append(exif_date)


    # Check modified/created/exif dates and get the earliest
    item_pathlib = Path(file_path)

    modified = datetime.fromtimestamp(item_pathlib.stat().st_mtime)
    dates.append(modified)

    created = datetime.fromtimestamp(item_pathlib.stat().st_ctime)
    dates.append(created)

    min_date = min(dates)
    max_date = max(dates)
    number_of_days = (max_date - min_date).days

    change_required = False
    if number_of_days > 0:
        change_required = True        

    return min_date, change_required
