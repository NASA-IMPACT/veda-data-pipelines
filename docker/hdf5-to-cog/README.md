# HDF5 to COG

Add to your `~/.netrc` file

```bash
machine urs.earthdata.nasa.gov
	login aimeeb
	password XXX
```

Run the transofrm

```bash
# Test it
python3 run.py \
  -c GPM_3IMERGM \
  -f https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.06/2020/3B-MO.MS.MRG.3IMERG.20200501-S000000-E235959.05.V06B.HDF5
```