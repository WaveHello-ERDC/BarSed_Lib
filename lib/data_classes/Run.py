"""
Class to represent a Run of the wave flume in the BarSed dataset

Author: WaveHello

Date: 07/02/2024
"""
# Standard imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.io
from datetime import datetime, timedelta

# Library imports
from lib.data_classes.WaveGauge import WaveGauge
from lib.data_classes.WaveMaker import WaveMaker

class Run:
    # TODO: Update this so that a file directory is based and it does 
    # all the rest
    def __init__(self, id, wave_file_path):
        self.id   = id             # Holds the id of the run eg. RUN001
        self.wave_file_path = wave_file_path # Path to the mat file that contains the run's
                                             # wave data

         # Init variables for later storage
        self.datetime = None
        self.start_date = None
        self.num_times = None
        self.wave_gauges = []      # Variable to hold the wave gauge information
        self.num_wave_gauges = None
        self.wave_maker  = None    # Variable to hold the wave maker information
    def __str__(self) -> str:
        """
        Called when the print statement is used on the Run object.
        Returns some metadata about the Run object
        """
        return (f"id: {self.id}\n"
                f"Start Date: {self.start_date}\n"
                f"Wave Data File path: {self.wave_file_path}\n"
                )
    
    def load_wave_data(self):
        """
        Loads the wave data from the mat file and constructs:
            * wave_maker
            * wave_gauges
        """
        variable_names = ["date", "eta", "x", "y", "eta_wm", "x_wm"]
        
        # Load the .mat data into a dict
        mat_dict = scipy.io.loadmat(self.wave_file_path, variable_names = variable_names)
        
        # NOTE: WaveHello: Set the time offset. This was just from looking at the excel spreedsheet
        time_offset = -1.0 * (365 + 2)

        """ Unpack the dict """

        # Get the time
        mat_time = mat_dict["eta"]["date"][0][0][0].flatten()

        # Get the eta
        eta    = mat_dict["eta"]["eta"][0][0]
        # Get the x locations of the wave gauges
        x_loc  = mat_dict["eta"]["x"][0][0].flatten() 

        # Get the y-locations of the wave gauges
        y_loc  = mat_dict["eta"]["y"][0][0].flatten()

        # Get the Surface water elevation in front of the wave maker piston
        eta_wm = mat_dict["eta"]["eta_wm"][0][0].flatten()

        # Get the location of the piston wave maker
        x_wm   = mat_dict["eta"]["x_wm"][0][0].flatten()

        # Convert the time and store it
        self._convert_mat_time_and_store(time_offset, mat_time)

        # Construct the wave maker
        self._construct_wave_maker(eta_wm, x_wm)

        # Construct the wave gauges
        self._construct_wave_gauges(x_loc, y_loc, eta)

    def _convert_mat_time_and_store(self, time_offset, mat_time):
        """
        Convert the time from what it is in the mat file to th matching date time
        """

        # Apply the offset to the data, need an offset because python's earliest time is 
        # 1, 1, 1 instead of matlab 0, 0, 0 
        mat_time = mat_time + time_offset

        experiment_datetime = []

        # Choose the 
        start_date = datetime(1, 1, 1)

        for i, time in enumerate(mat_time):
            # Calc delta time from the 
            delta_datetime = timedelta(days = time)
            experiment_datetime.append(start_date + delta_datetime)

        # Store the full date time array
        self.datetime = experiment_datetime

        # Store the start date
        self.start_date = self.datetime[0].date()

        # Store the number of record times
        self.num_times = len(self.datetime)

    def _construct_wave_maker(self, eta_wm, x_wm):
        """
        Construct the wave maker
        """
        self.wave_maker = WaveMaker(eta_wm, x_wm, self.datetime)
    
    def _construct_wave_gauges(self, x_loc, y_loc, eta):
        """
        Construct the wave gauge objects and store them
        """

        # Init list for temp storage
        wave_gauge_list = []
        # Loop over the locations and construct the wave gauges 
        for id, location in enumerate(zip(x_loc, y_loc)):
    
            # Create the wave gauge
            wave_gauge = WaveGauge(id + 1, location, eta[id], self.datetime)
            
            # Store the wave gauge in the list
            wave_gauge_list.append(wave_gauge)
    
        # Add the wave gauges to the Run object
        self.add_wave_gauge(wave_gauge_list)

    def add_wave_maker(self, wave_maker):
        """
        Add wave maker object to the run
        """

        # Only WaveMaker objects should be passed here
        if isinstance(wave_maker, WaveMaker):
            # Store the WaveMaker in the Run object
            self.wave_maker = wave_maker
        else:
            # Raise an error if the type is wrong
            raise TypeError("Type must be WaveMaker."
                            f" Input type is {type(wave_maker)}")
        
    def add_wave_gauge(self, wave_gauge):
        # Store the wave information inside of the run
        # wave_gauge should be type(WaveGauge) or list

        if isinstance(wave_gauge, list):
            # If multiple wave gauges are being inputted in list concatenate them to the list
            self.wave_gauges = self.wave_gauges + wave_gauge

        elif isinstance(wave_gauge, WaveGauge):
            # if the only one wave gauge is being added just append it to the list
            self.wave_gauges.append(wave_gauge)

        else: 
            raise TypeError("The type must be a list or a WaveGauge object\n"
                            f"Input type is: {type(wave_gauge)}")

        # update the number of wave gauges
        self.num_wave_gauges = len(self.wave_gauges)
        print("New Number of {} wave gauges".format(self.num_wave_gauges))
   
    def construct_wave_gauge_wse(self):
        """
        Construct the water surface elevation (wse) across the entire flume 
        using the wave gauge data
        """

        # Init array to store the surface elevations
        surface_elevations = np.zeros((self.num_times, self.num_wave_gauges))

        # Loop over the wave gauges
        for i, wave_gauge in enumerate(self.wave_gauges):
            # Get the measured water surface
            surface_elevations[:, i] = wave_gauge.eta

        # Store the water surface elevations in the object
        self.wave_gauge_wse = surface_elevations

    def get_wave_gauge_locations(self):
        """
        Get and store the wave gauge locations
        """

        # Number of location dimensions
        num_dim = 2

        # init array to hold the location data
        location = np.zeros((self.num_wave_gauges, num_dim))

        # Set the column indices for where the x and y data should be written
        x_col = 0
        y_col = 1

        # Loop over the wave gauges and store there locations
        for i, wave_gauge in enumerate(self.wave_gauges):
            location[i, x_col] = wave_gauge.location[0]
            location[i, y_col] = wave_gauge.location[1]

        self.wg_locations = pd.DataFrame(location, columns = ["x_loc", "y_loc"])

    def construct_flume_wse(self):
        """
        Construct the wse across the entire flume
        This differs from construct construct_wave_gauge_wse in that it
        includes the surface elevation of the wave maker.
        This adds a little complexity because the location of the wave maker moves
        """
        # Just need to append the wave maker data to the gauge data
        
        x_location = np.zeros((self.num_times, self.num_wave_gauges + 1))
        water_surface_elevation = np.zeros((self.num_times, self.num_wave_gauges + 1))
        
        # Fill the x_location data
        x_location[:, 0]  = self.wave_maker.position

        x_location[:, 1:] = self.wg_locations["x_loc"]

        # Fill the wse data
        water_surface_elevation[:, 0]  = self.wave_maker.eta_wm
        water_surface_elevation[:, 1:] = self.wave_gauge_wse

        # Store the data in the object
        self.flume_wse = water_surface_elevation
        self.flume_wse_locs  = x_location

    def quick_flume_wse_plot(self, time_index, figsize = (8, 4), 
                             legend = False, **kwargs):
        """
        Plot the water surface elevation using the wave gauge data using a 
        """

        #Create the figure plot object
        fig, axs = plt.subplots(nrows = 1, ncols = 1, figsize = figsize)

        # If multiple times are inputted
        if isinstance(time_index, list):

            # Loop over the time indices ...
            for index in time_index:

                # Store the water surface elevation (wse) and the location
                wse = self.flume_wse[index, :]
                # Only the first location changes because the wave maker moves
                location = self.flume_wse_locs[index, :]

                # Construct the label for the data
                time_label = f"time: {self.datetime[index].time()}"
                
                # Plot the data
                axs.plot(location, wse, label = time_label, **kwargs)

        else:
            #Store the water surface elevation and the location of the measurements (x -direction)
            wse = self.flume_wse[time_index, :]
            location = self.flume_wse_locs[time_index, :]

            # Cosntruct the time label
            time_label = f"time: {self.datetime[time_index].time()}"

            # Plot the data
            axs.plot(location, wse, label = time_label, **kwargs)
        
        # Format the plot
        axs.set_xlabel("Cross-shore distance (m)")
        axs.set_ylabel("Water Surf. Elev. (m)")

        if legend:
            axs.legend()

    def quick_plot_wave_gauges(self, gauge_ids, figsize = (8, 6), 
                               legend = False, ylabel = True,
                               xlabel= True, time_units= "min", **kwargs):
        """
        Plot wave gauge data as a function of time
        """

        if isinstance(gauge_ids, list):
            num_gauges = len(gauge_ids)
        else:
            num_gauges = 1
            # Make the single value into list to make plotting easier
            gauge_ids = [gauge_ids]

        fig, axs = plt.subplots(nrows = num_gauges, ncols = 1, figsize= figsize)

        # Make sure the axs can be looped over even when there's only one plot being created
        axs = np.atleast_1d(axs)

        time= self.datetime

        # Loop over the ids
        for i, id in enumerate(gauge_ids):

            #TODO: Assumes that the wave gauges are in order
            # Which for the time being I'm going to live with
            # Have to shift the id value to match zero indexing
            wave_gauge = self.wave_gauges[id - 1]

            # Select the gauge
            axs[i].plot(time, wave_gauge.eta, label = f"{wave_gauge.id}")

            if ylabel:
                axs[i].set_ylabel("Water Surf. Elev. (m)")
            # Format the xlabel
            if xlabel:
                axs[i].set_xlabel(f"Time {time_units}")
            else:
                axs[i].set_xticklabels([])

            if legend:
                axs[i].legend()