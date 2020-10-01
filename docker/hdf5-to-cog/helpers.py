import os

def rename_imerg(filename, monthly = False):
    """
    This is specific to GPM IMERG product
    """
    imerg_date = filename.split(".")[4].split('-')[0]
    replacement_date = f"{imerg_date[0:4]}_{imerg_date[4:6]}_{imerg_date[6:8]}"
    if monthly:
        replacement_date = f"{imerg_date[0:4]}{imerg_date[4:6]}"
    else:
        replacement_date = f"{imerg_date[0:4]}_{imerg_date[4:6]}_{imerg_date[6:8]}"
    replaced_date_filename = filename.replace(imerg_date, replacement_date)
    # Removing some trailing identifiers for IMERG monthly
    return f"{os.path.splitext('.'.join(replaced_date_filename.split('.')[:-2]))[0]}.tif"