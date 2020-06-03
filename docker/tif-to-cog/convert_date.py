import datetime
import argparse
import os

parser = argparse.ArgumentParser(description="Generate COG from .img file and schema")
parser.add_argument("-f", "--filename", help="filename to convert")
args = parser.parse_args()

filename = args.filename
monthyear = filename.split('_')[-2].split('.')[0]
formatted_date = datetime.datetime.strptime("{0}".format(monthyear), "%b%Y").strftime("%Y_%m_%d")
new_filename = filename.replace(monthyear, formatted_date)
os.rename(filename, new_filename)
print(new_filename)
