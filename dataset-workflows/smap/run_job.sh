#!/usr/bin/env bash
#SBATCH --account=s3673
#SBATCH --constraint='sky|hasw'
#SBATCH --time=60
#SBATCH --mem=32G

mod_python

echo "Python: $(which python)"
echo "Working directory: $(pwd)"

echo "Starting script"
python 02-create-zarr.py
echo "Done!"
exit
