from osgeo import gdal
import argparse

parser = argparse.ArgumentParser(description="Generate COG from file and schema")
parser.add_argument("--fromfile", help="file to take band descriptions from")
parser.add_argument("--tofile", help="file to write band descriptions to")
parser.add_argument("-n", "--num_bands", type=int, help="Number of bands to describe")
args = parser.parse_args()

# Adds band descriptions from fromfile to outfile
# Intended for writing band descriptions from a source TIF to a composite COG
# Currently not working to maintain valid COG
# The following errors were found:
# - The offset of the main IFD should be 8 for ClassicTIFF or 16 for BigTIFF. It is 4435584 instead
# - The offset of the IFD for overview of index 0 is 4868, whereas it should be greater than the one of the main image, which is at byte 4435584

infile = gdal.Open(args.fromfile.replace("hdf", "tif"), gdal.GA_ReadOnly)
outfile = gdal.Open(args.tofile, gdal.GA_Update)

for bidx in range(args.num_bands):
    outfile.GetRasterBand(bidx+1).SetDescription(infile.GetRasterBand(bidx+1).GetDescription())

