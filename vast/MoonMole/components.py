""" Define functional object types to be used for simulating lunar mining operation.
Lunar mining uses two components, "Trucks" and "Stations".
Stations are fixed locations where ore is ingested and stored.
Trucks move back and forth between Stations and Mining sites.
"""

from enum import Enum, unique, auto
import random
from dataclasses import dataclass


@unique
class TruckStatus(Enum):
  """
      Static states that a truck can exist in.
      All trucks should always be in exactly one state.
  """
  IDLE = auto()
  MINING = auto()
  UNLOADING = auto()
  TRAVELING_TO_MINE = auto()
  TRAVELING_TO_STATION = auto()

@unique
class StationStatus(Enum):
  """
      Static states that a station can exist in.
      All stations should always be in exactly one state.
      This could be a boolean, but an enum allows future growth.
  """
  IDLE = auto()
  BUSY = auto()

@dataclass
class MiningRun:
  """ Tracking data for overall run of multiple stations and multiple trucks.
  """
  # pylint: disable=too-many-instance-attributes
  # This data class defines the entire simulation, so has many parameters.
  num_stations: int = 0
  num_trucks: int = 0
  run_hours: int = 0
  total_loads_collected: int = 0
  total_load_count: int = 0
  total_idle_truck_time: int = 0
  total_busy_truck_time: int = 0
  total_idle_station_time: int = 0
  total_busy_station_time: int = 0
  verbose_trucks: bool = False
  verbose_stations: bool = False
  min_mining_hours: int = 1
  max_mining_hours: int = 5
  slice_time: int = 5

  def run_minutes(self) -> int:
    """ For human readable output.
    """
    return self.run_hours * 60

  def run_time_slices(self) -> int:
    """ Because every defined action is divisible by 5, five minute time slices make sense.
    """
    # ToDo: If the defined time parameters change, this constant will need to change.
    return self.run_hours * int(60/self.slice_time)

  # ToDo:  This might belong in the 'Truck' object.
  def generate_mining_time(self) -> int:
    """ Simulation specifies that mining will take between one and five hours.
    """
    # ToDo:  If Truck operating times are likely to change, this should be expanded.
    return random.randint(self.min_mining_hours, self.max_mining_hours) * 60

  def generate_truck_efficiency(self) -> int:
    """ Calculate the percent of time a truck spends mining.
    """
    average_busy_minutes_per_truck = self.total_busy_truck_time/self.num_trucks
    average_ratio_of_busy_minutes = average_busy_minutes_per_truck/self.run_minutes()
    percent_busy_time = round(100 * average_ratio_of_busy_minutes)
    return percent_busy_time

  def generate_station_efficiency(self) -> int:
    """ Calculate the percent of time a station spends unloading.
    """
    average_busy_minutes_per_station = self.total_busy_station_time/self.num_stations
    average_ratio_of_busy_minutes = average_busy_minutes_per_station/self.run_minutes()
    percent_busy_time = round(100 * average_ratio_of_busy_minutes)
    return percent_busy_time

  def generate_report(self) -> str:
    """ Returns a formatted string with summary information from the full test run.
    """
    return ('Results from simulated mining run.\n'
            f'{self.run_hours} hour run {self.total_load_count} truck loads of ore delivered.\n'
            f'{self.num_trucks} Trucks, {self.num_stations} Stations.\n'
            f'Trucks operated at {self.generate_truck_efficiency()} percent efficiency, measured as hours'
             ' spent actively mining over the full run time.\n'
            f'Stations operated at {self.generate_station_efficiency()} percent efficiency, measured as hours'
             ' spent actively unloading ore over the full run time.\n'
           )

  def generate_csv_report(self) -> str:
    """ Returns a comma separated string for storing in files.
    """
    return (f'Run Summary,Total Loads Of Ore:,{self.total_load_count},Station Count,{self.num_stations},'
            f'Mining Truck Count,{self.num_trucks}\nTruck Efficiency,{self.generate_truck_efficiency()},'
            f'Station Efficiency,{self.generate_station_efficiency()}\n')

class Truck():
  """
      Truck is a simulated mining unit. 
      It can be actively mining, moving to or from an unloading station,
      unloading at a station, or idle waiting for a station.
      Each of these activities takes a preset period of time. With only 'mining' having a variable length.
  """
  # pylint: disable=too-many-instance-attributes
  # Truck is they core functional component of this project, so is somewhat complex.
  state: TruckStatus
  name: str
  time_logs: dict
  completed_loads: int
  current_mining_time: int
  verbose: bool
  run_parameters: MiningRun

  def __init__(self, simulation_parameters, name='unnamed'):
    self.name = name
    # ToDo: Replace 'time_logs' dict with regular object attributes.
    self.time_logs: dict = {t.name: 0 for t in TruckStatus}
    # Per simulation specification, trucks start at the mining site.
    self.state = TruckStatus.MINING
    self.completed_loads = 0

    self.simulation_parameters = simulation_parameters
    # ToDo:  These two could probably use simulation_parameters directly.
    self.verbose = simulation_parameters.verbose_trucks
    self.remaining_time = self.simulation_parameters.generate_mining_time()

    self.current_cycle_mining_time = self.remaining_time

  def __str__(self):
    return (f'Truck Name: {self.name}\nTruck State: {self.state.name}\nRemaining time in state: {self.remaining_time}'
            f' Completed_Loads: {self.completed_loads}\nTotal Time in state: {self.time_logs}')

  def get_available_station(self, stations: list['Station']):
    """ Check station status and return the first available station, or none if all stations are busy.
    """
    for station in stations:
      if station.state == StationStatus.BUSY:
        if self.verbose:
          print(f'Station {station.name} is busy, servicing {station.attached_truck.name}')
      else:
        if self.verbose:
          print(f'Station {station.name} is idle, attaching {self.name}')
        return station
    if self.verbose:
      print('No available stations')
    return None

  def transition_from_mining(self):
    """ When a truck is full, begin moving it to the stations.
    """
    self.time_logs['MINING'] += self.current_cycle_mining_time
    self.state = TruckStatus.TRAVELING_TO_STATION
    self.remaining_time = self.simulation_parameters.inbound_travel_time

  def transition_from_inbound(self, stations: list['Station']):
    """
        When a truck arrives at the stations, assign to an available station.
        If no stations are available, set truck to idle.
    """
    self.time_logs['TRAVELING_TO_STATION'] += self.simulation_parameters.inbound_travel_time
    if station := self.get_available_station(stations):
      if self.verbose:
        print(f'Attaching {self.name} to {station.name}')
      station.attach(self)
      self.state = TruckStatus.UNLOADING
      self.remaining_time = self.simulation_parameters.unloading_time
    else:
      if self.verbose:
        print('No station available for {self.name} switching to idle state and waiting five minutes')
      self.state = TruckStatus.IDLE
      self.remaining_time = self.simulation_parameters.idle_wait_time

  def transition_from_unloading(self):
    """ When a truck is empty, send it back to the mining site. 
    """
    self.time_logs['UNLOADING'] += self.simulation_parameters.unloading_time
    self.completed_loads += 1
    self.state = TruckStatus.TRAVELING_TO_MINE
    self.remaining_time = self.simulation_parameters.outbound_travel_time

  def transition_from_idle(self, stations: list['Station']):
    """ When a truck has been idling, assign to an available station.
        If no stations are available, reset the idle time
    """
    self.time_logs['IDLE'] += self.simulation_parameters.idle_wait_time
    # Transition From Inbound and Transition from Idle are the same activity.
    self.transition_from_inbound(stations)

  def transition_from_outbound(self):
    """ When a truck arrives at the mining site, determine how long it needs to stay.
        Then set time and state.
    """
    self.time_logs['TRAVELING_TO_MINE'] += self.simulation_parameters.outbound_travel_time
    self.state = TruckStatus.MINING
    self.remaining_time = self.simulation_parameters.generate_mining_time()
    self.current_cycle_mining_time = self.remaining_time

  def cycle(self, stations: list['Station']):
    """
        Move time forward by one five minute slice. 
        If the truck has remaining time of zero, transition it to it's next state.
    """
    # This could be written as "> 0" but that is slightly more computationally intensive.
    if self.remaining_time:
      if self.verbose:
        print(f'{self.name} Stay in state {self.state.name} for {self.remaining_time} minutes')
      self.remaining_time -= self.simulation_parameters.slice_time
    else:
      match self.state:
        case TruckStatus.MINING:
          self.transition_from_mining()

        case TruckStatus.TRAVELING_TO_STATION:
          self.transition_from_inbound(stations)

        case TruckStatus.UNLOADING:
          self.transition_from_unloading()

        case TruckStatus.IDLE:
          self.transition_from_idle(stations)

        case TruckStatus.TRAVELING_TO_MINE:
          self.transition_from_outbound()

  def generate_report(self) -> str:
    """Deliver a self status report.
    """
    ratio_of_time_mining = self.time_logs['MINING'] / self.simulation_parameters.run_minutes()
    percent_of_time_mining = round(ratio_of_time_mining * 100)

    return (f'Status report for truck: {self.name}\n'
            f'Time spent mining. Total: {round(self.time_logs["MINING"]/60)} hours. Percent: {percent_of_time_mining}\n'
            f'Loads of Ore delivered: {self.completed_loads}\n')


class Station():
  """
      Station simulates a simple ingest and storage system for ore.
      A station is either 'busy' or 'idle'.
      Idle stations can accept ore from a truck, busy stations cannot.
      Busy stations transition to idle after an unloading period. (initially five minutes)
  """
  state: StationStatus
  name: str
  busy_minutes: int
  idle_minutes: int
  attached_truck: Truck | None
  verbose: bool
  completed_loads: int
  run_parameters: MiningRun

  def __init__(self, simulation_parameters, name='unnamed', verbose=False):
    self.name = name
    self.busy_minutes = 0
    self.idle_minutes = 0
    self.state = StationStatus.IDLE
    self.attached_truck = None
    # ToDo: Use simulation_parameters directly instead of a separate parameter.
    self.verbose = verbose
    self.simulation_parameters = simulation_parameters
    self.completed_loads = 0

  def __str__(self):
    msg = ( f'Station Name: {self.name}\n'
            f'Station status: {self.state}\n'
            f'\nTotal Time in state: BUSY:{self.busy_minutes} IDLE:{self.idle_minutes}\n')
    if self.attached_truck:
      msg += f'Unloading {self.attached_truck.name}\n'
    return msg

  def attach(self, truck: Truck):
    """ Attach a truck to a station.
    """
    if self.verbose:
      print(f'Attaching {truck.name} to {self.name}')
    self.attached_truck = truck
    self.state = StationStatus.BUSY

  def release(self):
    """ Release an attached truck.
    """
    if self.verbose:
      print(f'Releaseing {self.attached_truck.name} from {self.name}')
    self.state = StationStatus.IDLE
    self.completed_loads += 1
    self.attached_truck = None

  def cycle(self):
    """ Move Busy stations to idle, or record idle time.
    """
    if self.state == StationStatus.BUSY:
      self.busy_minutes += self.simulation_parameters.slice_time
      self.release()
    else:
      self.idle_minutes += self.simulation_parameters.slice_time

  def generate_report(self) -> str:
    """Deliver a self status report.
    """
    ratio_of_time_unloading = self.busy_minutes / self.simulation_parameters.run_minutes()
    percent_of_time_unloading = round(ratio_of_time_unloading * 100)

    return (f'Status report for station: {self.name}\n'
            f'Time spent unloading. Total: {round(self.busy_minutes/60)} hours.'
            f' Percent: {percent_of_time_unloading}\n'
            f'Loads of Ore unloaded: {self.completed_loads}\n')
