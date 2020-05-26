import numpy as np
import scipy.ndimage
import math

def select_from_orbits(args, hdf_file, data_var):
    """
    Given a data var is part of a subdataset with multiple orbits, select data
    from the orbit which had the minimum angle for `orbit_sds_name`.
    """
    orbit_data = hdf_file.select(args['orbit_sds_name'])
    # First dimension is the number of orbits
    # To get the scale factor
    orbit_height = orbit_data.dim(1).length()
    orbit_width = orbit_data.dim(2).length()
    # TODO: Not DRY - we recalculate src_width and src_height here
    src_width = data_var.dim(1).length()
    src_height = data_var.dim(2).length()    
    upscale_height_factor = src_height / orbit_height
    upscale_width_factor = src_width / orbit_width

    # num_orbits x src_height x src_width grid
    angle_scale_factor = orbit_data.attributes()["scale_factor"]
    angle_nodata = orbit_data.getfillvalue()
    def mycos(v):
        if v == angle_nodata:
            return angle_nodata
        try: 
            return np.abs((math.acos(v*angle_scale_factor)) * (180 / np.pi))
        except Exception as e:
            return angle_nodata

    angles = np.vectorize(mycos)(orbit_data[:])
    # Fix me!!! ignore any angles which are invalid (nodata values)
    angles[angles == angle_nodata] = 1000
    orbit_resampled = scipy.ndimage.zoom(
        angles,
        (1, upscale_height_factor, upscale_width_factor),
        order=0
    )
    orbit_min_indices = np.argmin(orbit_resampled, axis=0)
    return np.choose(orbit_min_indices, data_var[:])
