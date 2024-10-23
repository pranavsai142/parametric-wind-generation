#!/usr/bin/env python3
# Contact: Josh Port (joshua_port@uri.edu) (MODIFICATIONS FOR OWI)
# Requirements: python3, numpy, netCDF4, scipy
#
# Converts OWI-NWS12 (ASCII) data to OWI-NWS13 (NetCDF) format
# Based on the COAMPS-TC to OWI converter by Zach Cobell
#
import datetime
import numpy
class WindGrid:
    def __init__(self, lon, lat):
#         print(lon, lat)
        import numpy
        self.__n_longitude = len(lon)
        self.__n_latitude = len(lat)
        self.__d_longitude = round(lon[1] - lon[0], 4)
        self.__d_latitude = round(lat[1] - lat[0], 4)
        self.__lon = lon
        self.__lat = lat
#         self.__lon = numpy.empty([self.__n_latitude, self.__n_longitude], dtype=numpy.float64)
#         self.__lat = numpy.empty([self.__n_latitude, self.__n_longitude], dtype=numpy.float64)
#         lon = numpy.array(lon)
#         lat = numpy.array(lat)
        lon = numpy.where(lon > 180, lon - 360, lon)
        self.__xll = min(lon)
        self.__yll = min(lat)
        self.__xur = max(lon)
        self.__yur = max(lat)
#         self.__lon,self.__lat = numpy.meshgrid(lon,lat) #sparse=True is an avenue to explore for saving memory
#         self.__lon1d = numpy.array(lon)
#         self.__lat1d = numpy.array(lat)

    def lon(self):
        return self.__lon

    def lat(self):
        return self.__lat

    def lon1d(self):
        return self.__lon1d

    def lat1d(self):
        return self.__lat1d

    def d_longitude(self):
        return self.__d_longitude

    def d_latitude(self):
        return self.__d_latitude

    def n_longitude(self):
        return self.__n_longitude

    def n_latitude(self):
        return self.__n_latitude

    def xll(self):
        return self.__xll

    def yll(self):
        return self.__yll

    def xur(self):
        return self.__xur

    def yur(self):
        return self.__yur

    @staticmethod
    def generate_equidistant_grid(grid=None,xll=None,yll=None,xur=None,yur=None,dx=None,dy=None):
        if grid:
            return WindGrid.__generate_equidistant_grid_from_grid(grid)
        if xll and yll and xur and yur and dx and dy:
            return WindGrid.__generate_equidistant_grid_from_corners(xll,yll,xur,yur,dx,dy)
        raise RuntimeError("No valid function call provided")

    @staticmethod
    def __generate_equidistant_grid_from_grid(grid):
        import numpy as np
        x = np.arange(grid.xll(), grid.xur(), grid.d_longitude())
        y = np.arange(grid.yll(), grid.yur(), grid.d_latitude())
        return WindGrid(x,y)

    @staticmethod
    def __generate_equidistant_grid_from_corners(x1,y1,x2,y2,dx,dy):
        import numpy as np
        x = np.arange(x1,x2,dx)
        y = np.arange(y1,y2,dy)
        return WindGrid(x,y)

    @staticmethod
    def interpolate_to_grid(original_grid, original_data, new_grid):
        from scipy import interpolate
        func = interpolate.interp2d(original_grid.lon1d(),original_grid.lat1d(),original_data,kind='linear')
        return func(new_grid.lon1d(),new_grid.lat1d())


class WindData:
    def __init__(self, date, wind_grid, pressure, u_velocity, v_velocity):
        import numpy
        self.__pressure = pressure
        self.__u_velocity = numpy.array(u_velocity)
        self.__v_velocity = numpy.array(v_velocity)
        self.__date = date
        self.__wind_grid = wind_grid

    def date(self):
        return self.__date

    def wind_grid(self):
        return self.__wind_grid
    
    def pressure(self):
        return self.__pressure    

    def u_velocity(self):
        return self.__u_velocity

    def v_velocity(self):
        return self.__v_velocity


class OwiNetcdf:
    def __init__(self, filename, wind_grid, bounds):
        import netCDF4
        from datetime import datetime
        self.__filename = filename
        self.__wind_grid = wind_grid
        self.__bounds = bounds
        self.__nc = netCDF4.Dataset(self.__filename + ".nc", "w")
        self.__conventions = "OWI-NWS13"
        self.__nc.source = "OWI ASCII to OWI NetCDF converter"
        self.__nc.author = "Josh Port"
        self.__nc.contact = "joshua_port@uri.edu"
            
        if self.__bounds:
            self.__equidistant_wind_grid = WindGrid.generate_equidistant_grid(
                                        xll=self.__bounds[0],yll=self.__bounds[1],
                                        xur=self.__bounds[2],yur=self.__bounds[3],
                                        dx=self.__bounds[4],dy=self.__bounds[5])

        # Create dimensions
        self.__nc_dim_time = self.__nc.createDimension("time", None)
        if self.__bounds:
            self.__nc_dim_longitude = self.__nc.createDimension("longitude", self.__equidistant_wind_grid.n_longitude())
            self.__nc_dim_latitude = self.__nc.createDimension("latitude", self.__equidistant_wind_grid.n_latitude())
        else:
            self.__nc_dim_longitude = self.__nc.createDimension("longitude", self.__wind_grid.n_longitude())
            self.__nc_dim_latitude = self.__nc.createDimension("latitude", self.__wind_grid.n_latitude())

        # Create variables (with compression)
        self.__nc_var_time = self.__nc.createVariable("time", "i4", "time", zlib=True, complevel=2,
                                                                      fill_value=netCDF4.default_fillvals["i4"])
        self.__nc_var_lon = self.__nc.createVariable("lon", "f8", ("longitude"), zlib=True, complevel=2,
                                                                     fill_value=netCDF4.default_fillvals["f8"])
        self.__nc_var_lat = self.__nc.createVariable("lat", "f8", ("latitude"), zlib=True, complevel=2,
                                                                     fill_value=netCDF4.default_fillvals["f8"])
        self.__nc_var_psfc = self.__nc.createVariable("PSFC", "f4", ("time", "latitude", "longitude"), zlib=True,
                                                                      complevel=2,
                                                                      fill_value=netCDF4.default_fillvals["f4"]) #This will be NaN throughout. Keeping to meet OWI-NWS13 format.
        self.__nc_var_u10 = self.__nc.createVariable("wind_u", "f4", ("time", "latitude", "longitude"), zlib=True,
                                                                     complevel=2,
                                                                     fill_value=netCDF4.default_fillvals["f4"])
        self.__nc_var_v10 = self.__nc.createVariable("wind_v", "f4", ("time", "latitude", "longitude"), zlib=True,
                                                                     complevel=2,
                                                                     fill_value=netCDF4.default_fillvals["f4"])

        # Add attributes to variables
        self.__base_date = datetime(1990, 1, 1, 0, 0, 0)
        self.__nc_var_time.units = "minutes since 1990-01-01 00:00:00 Z"
        self.__nc_var_time.axis = "T"
        self.__nc_var_time.coordinates = "time"

        self.__nc_var_lon.coordinates = "lat lon"
        self.__nc_var_lon.units = "degrees_east"
        self.__nc_var_lon.standard_name = "longitude"
        self.__nc_var_lon.axis = "x"

        self.__nc_var_lat.coordinates = "lat lon"
        self.__nc_var_lat.units = "degrees_north"
        self.__nc_var_lat.standard_name = "latitude"
        self.__nc_var_lat.axis = "y"
        
        self.__nc_var_psfc.units = "mb"
        self.__nc_var_psfc.coordinates = "time lat lon"        

        self.__nc_var_u10.units = "m s-1"
        self.__nc_var_u10.coordinates = "time lat lon"

        self.__nc_var_v10.units = "m s-1"
        self.__nc_var_v10.coordinates = "time lat lon"

        if self.__bounds:
            self.__nc_var_lat[:] = self.__equidistant_wind_grid.lat()
            self.__nc_var_lon[:] = self.__equidistant_wind_grid.lon()
        else:
            self.__nc_var_lat[:] = wind_grid.lat()
            self.__nc_var_lon[:] = wind_grid.lon()

    def append(self, idx, wind_data):
        delta = (wind_data.date() - self.__base_date)
        minutes = round((delta.days * 86400 + delta.seconds) / 60)

        if self.__bounds:
            press = WindGrid.interpolate_to_grid(wind_data.wind_grid(),wind_data.pressure(),self.__equidistant_wind_grid)
            u_vel = WindGrid.interpolate_to_grid(wind_data.wind_grid(),wind_data.u_velocity(),self.__equidistant_wind_grid)
            v_vel = WindGrid.interpolate_to_grid(wind_data.wind_grid(),wind_data.v_velocity(),self.__equidistant_wind_grid)
        else:
            press = wind_data.pressure()
            u_vel = wind_data.u_velocity()
            v_vel = wind_data.v_velocity()

        self.__nc_var_time[idx] = minutes
        self.__nc_var_psfc[idx, :, :] = press
        self.__nc_var_u10[idx, :, :] = u_vel
        self.__nc_var_v10[idx, :, :] = v_vel

    def close(self):
        self.__nc.close()


class Owi306Wind:
    def __init__(self, win_filename, win_inp_filename):
        self.__input_file_lines = open(win_inp_filename, 'r').readlines()
        self.__start_time = None
        self.__time_delta = datetime.timedelta(seconds=3600)
        win_file = open(win_filename, 'r')
        self.__lines = win_file.readlines()
        win_file.close()
        self.__win_filename = win_filename
        self.__num_lats = None
        self.__num_lons = None
        self.__grid = self.__get_grid()

    def grid(self):
        return self.__grid

    def __get_grid(self):
#     Manually set parameters for 306 type file
        lines = self.__input_file_lines
        datepart = lines[2].split()
        self.__start_time = datetime.datetime(int(datepart[0]), int(datepart[1]), int(datepart[2]), int(datepart[3]), int(datepart[4]), int(datepart[5]))
        time_step = float(lines[3])
        num_times = int(lines[4])
        spatial_res = float(1 / float(lines[7].strip()))
        lat_bounds = lines[6].split()
        lon_bounds = lines[5].split()
        s_lim = float(lat_bounds[0])
        n_lim = float(lat_bounds[1])
        w_lim = float(lon_bounds[0])
        e_lim = float(lon_bounds[1])
        self.__num_lats = int((n_lim - s_lim) / spatial_res + 1)
        self.__num_lons = int((e_lim - w_lim) / spatial_res + 1)
#         num_lats = 277
#         num_lons = 325
#         lat_step = 0.150002
#         lon_step = 0.150002
        lat_step = spatial_res
        lon_step = spatial_res
#         nw_corner_lat = 46.400002
#         sw_corner_lat = 4.9995
#         sw_corner_lon = -98.6
        sw_corner_lat = s_lim
        sw_corner_lon = w_lim
        lat = numpy.linspace(sw_corner_lat, sw_corner_lat + (self.__num_lats - 1) * lat_step, self.__num_lats)
        lon = numpy.linspace(sw_corner_lon, sw_corner_lon + (self.__num_lons - 1) * lon_step, self.__num_lons)
        print("lat lon 0 -1 len", lat[0], lat[-1], len(lat), lon[0], lon[-1], len(lon))
        return WindGrid(lon, lat)

        
    def num_times(self):
        timesteps = int(len(self.__lines)/(self.__num_lats * self.__num_lons))
        return timesteps

    def get(self, idx):
        idx_date = (self.__time_delta * idx) + self.__start_time
#         print(idx_date)
        starting_row = idx * (self.__num_lats * self.__num_lons)
        ending_row = starting_row + (self.__num_lats * self.__num_lons)
        print(starting_row, ending_row)
        latitudeIndex = self.__num_lats - 1
        longitudeIndex = 0
        uvel = [[None for i in range(self.__num_lons)] for j in range(self.__num_lats)]
        vvel = [[None for i in range(self.__num_lons)] for j in range(self.__num_lats)]
        prmsl = [[None for i in range(self.__num_lons)] for j in range(self.__num_lats)]
#         print(len(uvel), len(uvel[0]))
        for index in range(starting_row, ending_row):
            if(longitudeIndex >= self.__num_lons):
                latitudeIndex = latitudeIndex - 1
                longitudeIndex = 0
#             print("index, latIndex, longIndex", index, latitudeIndex, longitudeIndex)
            data = self.__lines[index].split()
            uvel[latitudeIndex][longitudeIndex] = float(data[0])
            vvel[latitudeIndex][longitudeIndex] = float(data[1])
            prmsl[latitudeIndex][longitudeIndex] = float(data[2])
            longitudeIndex = longitudeIndex + 1  
        return WindData(idx_date, self.__grid, prmsl, uvel, vvel)


class OwiAscii:
    # NOTE: This class assumes the same number of grid points in each time slice.
    # The conversion will fail if this isn't the case.
    def __init__(self, pre_filename, win_filename, idx):
        self.__pre_filename = pre_filename
        self.__win_filename = win_filename
        self.__idx = idx
        self.__num_lats = self.__get_num_lats()
        self.__num_lons = self.__get_num_lons()
        self.__pre_idx_header_row = self.__get_pre_idx_header_row()
        self.__win_idx_header_row = self.__get_win_idx_header_row()
        self.__date = self.__get_date()
        self.__grid = self.__get_grid()

    def date(self):
        return self.__date

    def grid(self):
        return self.__grid
    
    def __get_num_lats(self):
        pre_file = open(self.__pre_filename, 'r')
        lines = pre_file.readlines()
        num_lats = lines[1][5:9]
        pre_file.close()
        return int(num_lats)
    
    def __get_num_lons(self):
        pre_file = open(self.__pre_filename, 'r')
        lines = pre_file.readlines()
        num_lons = lines[1][15:19]
        pre_file.close()
        return int(num_lons)    
            
    def __get_pre_idx_header_row(self):
        from math import ceil
        return 1 + ceil((self.__num_lats * self.__num_lons) / 8) * self.__idx + self.__idx
    
    def __get_win_idx_header_row(self):
        from math import ceil
        return 1 + 2 * ceil((self.__num_lats * self.__num_lons) / 8) * self.__idx + self.__idx

    def __get_date(self):
        from datetime import datetime
        pre_file = open(self.__pre_filename, 'r')
        lines = pre_file.readlines()
        date_str = lines[self.__pre_idx_header_row][68:80]
        idx_date = datetime(int(date_str[0:4]), int(date_str[4:6]), int(date_str[6:8]), int(date_str[8:10]), int(date_str[10:12]))
        pre_file.close()
        return idx_date
    
    def __get_grid(self):
        from numpy import linspace
        pre_file = open(self.__pre_filename, 'r')
        lines = pre_file.readlines()
        lat_step = float(lines[self.__pre_idx_header_row][31:37])
        lon_step = float(lines[self.__pre_idx_header_row][22:28])
        sw_corner_lat = float(lines[self.__pre_idx_header_row][43:51])
        sw_corner_lon = float(lines[self.__pre_idx_header_row][57:65])
        lat = linspace(sw_corner_lat, sw_corner_lat + (self.__num_lats - 1) * lat_step, self.__num_lats)
        lon = linspace(sw_corner_lon, sw_corner_lon + (self.__num_lons - 1) * lon_step, self.__num_lons)
        pre_file.close()
        return WindGrid(lon, lat)

    def get(self, idx):
        from math import ceil, floor
        pre_file = open(self.__pre_filename, 'r')
        lines = pre_file.readlines()
        prmsl = [[None for i in range(self.__num_lons)] for j in range(self.__num_lats)]
        for i in range(self.__num_lats * self.__num_lons):
            low_idx = 1 + 10 * (i % 8)
            high_idx = 10 + 10 * (i % 8)
            line_idx = self.__pre_idx_header_row + 1 + floor(i / 8)
            lon_idx = i % self.__num_lons
            lat_idx = floor(i / self.__num_lons)
            prmsl[lat_idx][lon_idx] = float(lines[line_idx][low_idx:high_idx])
        pre_file.close()
        
        win_file = open(self.__win_filename, 'r')
        lines = win_file.readlines()
        uvel = [[None for i in range(self.__num_lons)] for j in range(self.__num_lats)]
        for i in range(self.__num_lats * self.__num_lons):
            low_idx = 1 + 10 * (i % 8)
            high_idx = 10 + 10 * (i % 8)
            line_idx = self.__win_idx_header_row + 1 + floor(i / 8)
            lon_idx = i % self.__num_lons
            lat_idx = floor(i / self.__num_lons)
            uvel[lat_idx][lon_idx] = float(lines[line_idx][low_idx:high_idx])
        vvel = [[None for i in range(self.__num_lons)] for j in range(self.__num_lats)]
        for i in range(self.__num_lats * self.__num_lons):
            low_idx = 1 + 10 * (i % 8)
            high_idx = 10 + 10 * (i % 8)
            line_idx = self.__win_idx_header_row + 1 + floor(i / 8) + ceil((self.__num_lats * self.__num_lons) / 8) 
            lon_idx = i % self.__num_lons
            lat_idx = floor(i / self.__num_lons)
            vvel[lat_idx][lon_idx] = float(lines[line_idx][low_idx:high_idx])            
        win_file.close()        
                
        print(self.__date)
        return WindData(self.__date, self.__grid, prmsl, uvel, vvel)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert OWI output to alternate formats")

    # Arguments
    parser.add_argument("files", metavar="file", type=str, help="Files to be converted; must be exactly two with ""pre"" file listed first", nargs='+')
    parser.add_argument("-f", metavar="fmt", type=str,
                        help="Format of output file (netcdf). Default: netcdf",
                        default="netcdf")
    parser.add_argument("-o", metavar="outfile", type=str,
                        help="Name of output file to be created. Default: [fort].nc|[fort].221,.222|[fort].amu,amv,amp",
                        required=True, default="fort")
    parser.add_argument("-b", metavar="x1,y1,x2,y2,dx,dy", type=str, help="Bounding box. Default: None",default=None,nargs=6)

    # Read the command line arguments
    args = parser.parse_args()
    is306 = False
    file_list = args.files
    num_files = len(file_list)
    if num_files == 0:
        raise RuntimeError("No files found for conversion")
    if ["Inp" in file_list[1]]:
        is306 = True
    if num_files - 2 > 0:
        raise RuntimeError("Must specify exactly one 306 type file or two files with the ""pre"" file listed first")

    if args.b:
        bounds = [float(args.b[0]),float(args.b[1]),float(args.b[2]),
                  float(args.b[3]),float(args.b[4]),float(args.b[5])]
        if not len(bounds) == 6:
            raise RuntimeError("Incorrectly formatted bounding box")
    else:
        bounds = None

    output_format = args.f

    
    wind = None
#     If converting 306 type wind, comment out below block
    if(is306):
        owi_ascii = Owi306Wind(file_list[0], file_list[1])
        num_times = owi_ascii.num_times()
    else:
        pre_file = open(file_list[0], 'r')
        lines = pre_file.readlines()
        num_times = 0
        for line in lines:
            if line[0] == 'i':
                num_times += 1   
        pre_file.close()
    

    time_index = 0
    while time_index < num_times: #This, plus making OwiAscii time-slice specific, lets us maintain the old OwiNetcdf class granularity and diverge less from the original code
#        If running 306 wind, comment below line
        if(not is306):
            owi_ascii = OwiAscii(file_list[0], file_list[1], time_index)
        print("INFO: Processing time slice {:d} of {:d}".format(time_index + 1, num_times), flush=True)
        wind_data = owi_ascii.get(time_index)
        if not wind:
            if output_format == "netcdf":
                wind = OwiNetcdf(args.o, wind_data.wind_grid(), bounds)
            else:
                raise RuntimeError("Invalid output format selected")
        wind.append(time_index, wind_data)
        time_index += 1   
    
    wind.close()

if __name__ == '__main__':
    main()
