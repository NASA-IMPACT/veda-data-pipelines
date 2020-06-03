import datetime
import argparse
import os

parser = argparse.ArgumentParser(description="Generate COG from .img file and schema")
parser.add_argument("-f", "--filename", help="filename to convert")
args = parser.parse_args()

filename = args.filename
monthyear = filename.split('_')[-2].split('.')[0]
month_format = "%B" if 'April' in monthyear or 'March' in monthyear else "%b"
formatted_date = datetime.datetime.strptime("{0}".format(monthyear), f"{month_format}%Y").strftime("%Y_%m_%d")
new_filename = filename.replace(monthyear, formatted_date)
os.rename(filename, new_filename)
print(new_filename)
