""" Simulate a helium-3 mining operation.
Given a number of fixed assets, Mining Trucks and Unloading Stations, and a timeframe in hours
Calulate total loads of ore generated and efficent use of each component.
"""

import sys
from collections import Counter
import argparse
from components import Truck, Station, MiningRun, TruckStatus, StationStatus


CSV_FILENAME = "mining_report.csv"
# Making this a lambda keeps both pyunittest and flask happy. (Building a proper library would be out of scope.)
ARGS = lambda: None  # pylint: disable=unnecessary-lambda-assignment
ARGS.comment='Redefined in main for unit test purposes.'
ARGS.detail_report_trucks=False
ARGS.detail_report_stations=False

TIME_SLICE_REPORT_ORDER = [TruckStatus.MINING, TruckStatus.TRAVELING_TO_STATION, TruckStatus.IDLE,
    TruckStatus.UNLOADING, TruckStatus.TRAVELING_TO_MINE, StationStatus.BUSY, StationStatus.IDLE]

def initialize_time_slice_report() ->list:
  """ Create a data object to hold time series data about the simulation run.
  """
  time_slice_report = [['','Mining Truck','','','','','','Unloading Station'],['Slice Count']]
  for column in TIME_SLICE_REPORT_ORDER:
    time_slice_report[1].append(column.name)
  return time_slice_report

def initialize_simulation_definition()  -> MiningRun:
  """ Instantiate a simulation object specific for this run with basic simulation parameters.
      Then add default values.  (These could be constants, but that gets messy.).
  """

  # First instantiate the object using the command line parameters
  simulation_parameters = MiningRun(
      run_hours = ARGS.run_hours,
      num_trucks = ARGS.truck_count,
      num_stations = ARGS.station_count,
      verbose_trucks = ARGS.verbose_trucks,
      verbose_stations = ARGS.verbose_stations)

  # Second add constants as defined by the customer's design
  # ToDo:  Make these parameters modifiable at the command line.
  simulation_parameters.inbound_travel_time = 30
  simulation_parameters.outbound_travel_time = 30
  simulation_parameters.unloading_time = 5
  simulation_parameters.idle_wait_time = 5
  # All actions above are in multiples of five minutes, so that is a useful granularity.
  # Both for processing and reporting.
  # ToDo: If above parameters are made variable, change this to a calculated value.
  # (This code change will have effects throughout the codebase.)
  simulation_parameters.slice_time = 5
  return simulation_parameters

def initialize_trucks(simulation_parameters: MiningRun) -> list[Truck]:
  """ Instantiate simulated mining trucks.
  """
  # ToDo: Change this to a list comprehension.
  trucks = []
  for truck_num in range(simulation_parameters.num_trucks):
    trucks.append(Truck(simulation_parameters=simulation_parameters, name=f'truck {truck_num}'))
  return trucks

def initialize_unloading_stations(simulation_parameters: MiningRun) -> list[Station]:
  """ Instantiate simulated unloading stations.
  """
  # ToDo: Change this to a list comprehension.
  stations = []
  for station_num in range(simulation_parameters.num_stations):
    stations.append(Station(simulation_parameters=simulation_parameters, name=f'station {station_num}',
        verbose=simulation_parameters.verbose_stations))
  return stations

def run_simulation(simulation_parameters: MiningRun, stations: list[Station], trucks: list[Truck]) -> list:
  """ Step through the simulated run in five minute slices.
  """
  time_slice_report = initialize_time_slice_report()

  # Loop through the simulation time in five minute slices.
  for time_slice in range(simulation_parameters.run_time_slices()):
    slice_report = Counter()

    # First process stations, so that busy stations can be idled.
    for station in stations:
      station.cycle()

    # Second move truck between various tasks.
    for truck in trucks:
      truck.cycle(stations)
      # Update counter for how much time each truck spends in each state.
      slice_report[truck.state] += 1

    # Third pass through stations again, recording status.
    for station in stations:
      # Update counter for how much time each station spends in each state.
      # We do this in a separate pass since all stations become idle for each slice.
      slice_report[station.state] += 1

    # Copy individual time slice data into time series data object.
    time_slice_report_line = [time_slice]
    for reportable_activity in TIME_SLICE_REPORT_ORDER:
      # If any instances of each activity have been recorded, copy that to the CSV.
      if activity_count := slice_report[reportable_activity]:
        time_slice_report_line.append(activity_count)
      else:
        # Otherwise record 0.
        time_slice_report_line.append(0)
    time_slice_report.append(time_slice_report_line)
  return time_slice_report

def summarize_truck_results(simulation_parameters: MiningRun, trucks: list[Truck]):
  """ Summarize truck results.
  """
  for truck in trucks:
    simulation_parameters.total_load_count += truck.completed_loads
    # ToDo: Change the 'time_logs' to full attibutes. Do this everywhere.
    # Adding that here, since this is the first place in the code 'time_logs' is mentioned.
    simulation_parameters.total_idle_truck_time += truck.time_logs['IDLE']
    simulation_parameters.total_busy_truck_time += truck.time_logs['MINING']
    if ARGS.detail_report_trucks:
      print(truck.generate_report())

def summarize_station_results(simulation_parameters: MiningRun, stations: list[Station]):
  """ Summarize station results.
  """
  for station in stations:
    # ToDo: Change the 'time_logs' to full attibutes. Do this everywhere.
    simulation_parameters.total_idle_station_time += station.idle_minutes
    simulation_parameters.total_busy_station_time += station.busy_minutes
    if ARGS.detail_report_stations:
      print(station.generate_report())

def generate_final_report_and_csv_file(simulation_parameters: MiningRun, time_slice_report: list):
  """ Generate, Print, and Write CSV time slide report.
  """
  with open(CSV_FILENAME, 'w', encoding='utf-8') as report_file:
    report_file.write(simulation_parameters.generate_csv_report())
    for slice_line in time_slice_report:
      report_file.write(','.join(map(str,slice_line))+'\n')

def parse_args():
  """ Define command line parameters. When called deliver parameters in a parameter object.
  """
  parser = argparse.ArgumentParser(prog='simulate', usage=r'%(prog)s [options]')

  parser.add_argument('--run_hours',  type=int, default=72,
    help='Define total time to run simulation in hours. (int)')
  parser.add_argument('--truck_count',  type=int, default=1,
    help='Define number of mining trucks to include in the simulation. (int)')
  parser.add_argument('--station_count',  type=int, default=1,
    help='Define number of unloading stations to include in the simulation, (int)')
  parser.add_argument('--verbose_trucks', action='store_true',
    help='Print truck transitions and actions during simulation run. (flag)')
  parser.add_argument('--verbose_stations', action='store_true',
    help='Print station transitions and actions during simulation run. (flag)')
  parser.add_argument('--detail_report_trucks', action='store_true',
    help='Print individual truck report after simulation run. (flag)')
  parser.add_argument('--detail_report_stations', action='store_true',
    help='Print individual station report after simulation run. (flag)')

  return parser.parse_args()

def simulation(simulation_parameters: MiningRun):
  """ Assign variables, generate and run report.
  """
  # Initialize simulated devices.
  trucks = initialize_trucks(simulation_parameters)
  stations = initialize_unloading_stations(simulation_parameters)

  # Run actual simulation.
  time_slice_report = run_simulation(simulation_parameters, stations, trucks)

  # Generate and deliver reports
  summarize_truck_results(simulation_parameters, trucks)
  summarize_station_results(simulation_parameters, stations)
  generate_final_report_and_csv_file(simulation_parameters, time_slice_report)

  return simulation_parameters

def main():
  """ Set up, run, then report on a simulated mining run.
  """
  # Ingest Parameters
  # pylint: disable=global-statement
  # Specifically setting the global 'ARGS' to make unit testing more straightforward.
  global ARGS
  ARGS = parse_args()
  simulation_parameters = initialize_simulation_definition()
  simulation_parameters = simulation(simulation_parameters)

  print(simulation_parameters.generate_report())

if __name__ == '__main__':
  sys.exit(main())
