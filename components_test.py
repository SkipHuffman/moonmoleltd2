""" Unit tests for components of moon mining simulator.
For portablity I have used only the most basic pytest functions.
No Mocks, or Magic, or fancy assert types. Only the most simple.
"""
# pylint: disable=missing-function-docstring,invalid-name

import components

def test_TruckStatus():
  assert components.TruckStatus.IDLE
  assert components.TruckStatus.MINING
  assert components.TruckStatus.UNLOADING
  assert components.TruckStatus.TRAVELING_TO_MINE
  assert components.TruckStatus.TRAVELING_TO_STATION

def test_StationStatus():
  assert components.StationStatus.IDLE
  assert components.StationStatus.BUSY

def test_MiningRun_RunTime():
  run = components.MiningRun(run_hours=1)
  assert run.run_minutes() == 60
  assert run.run_time_slices() == 12

def test_MiningRun_mining_time():
  run = components.MiningRun()
  assert 60 <= run.generate_mining_time() <= 300

def test_MiningRun_truck_efficency():
  run = components.MiningRun(
            num_trucks=1,
            run_hours=1,
            total_busy_truck_time=60,
        )
  assert run.generate_truck_efficiency() == 100

def test_MiningRun_station_efficency():
  run = components.MiningRun(
            num_stations=1,
            run_hours=1,
            total_busy_station_time=60,
        )
  assert run.generate_station_efficiency() == 100

def test_MiningRun_generate_report():
  run = components.MiningRun(
            num_stations=1,
            run_hours=1,
            total_busy_station_time=60,
            num_trucks=1,
            total_busy_truck_time=60,
        )
  expected = ('Results from simulated mining run.\n'
              '1 hour run 0 truck loads of ore delivered.\n'
              '1 Trucks, 1 Stations.\n'
              'Trucks operated at 100 percent efficiency, measured as hours spent actively mining over the full'
              ' run time.\n'
              'Stations operated at 100 percent efficiency, measured as hours spent actively unloading ore over'
             ' the full run time.\n'
             )
  assert run.generate_report() == expected

def test_MiningRun_generate_csv_report():
  run = components.MiningRun(
            num_stations=1,
            run_hours=1,
            total_busy_station_time=60,
            num_trucks=1,
            total_busy_truck_time=60,
        )
  expected = ('Run Summary,Total Loads Of Ore:,0,Station Count,1,Mining Truck Count,1\n'
              'Truck Efficiency,100,Station Efficiency,100\n'
             )
  assert run.generate_csv_report() == expected

def test_Truck_print():
  run = components.MiningRun()
  run.remaining_time_in_state = 60
  truck = components.Truck(run)

  expected = ['Truck Name: unnamed',
              'Truck State: MINING',
              'Remaining time in state: 60 Completed_Loads: 0', # Will not be used, value has a random number in it.
              "Total Time in state: {'IDLE': 0, 'MINING': 0, 'UNLOADING': 0, 'TRAVELING_TO_MINE': 0,"
              " 'TRAVELING_TO_STATION': 0}"
             ]
  assert f'{truck}'.split('\n', maxsplit=1)[0] == expected[0]
  assert f'{truck}'.split('\n')[1] == expected[1]
  # Cannot check this line since it contains a random value.
  assert f'{truck}'.split('\n')[3] == expected[3]

def test_Truck_get_available_stations_available():
  run = components.MiningRun()
  run.remaining_time_in_state = 60
  truck = components.Truck(run)
  station = components.Station(run)
  stations = [station]

  assert truck.get_available_station(stations) == station

def test_Truck_get_available_stations_not_available():
  run = components.MiningRun()
  run.remaining_time_in_state = 60
  truck = components.Truck(run)
  station = components.Station(run)
  station.state = components.StationStatus.BUSY
  stations = [station]

  assert truck.get_available_station(stations) is None

def test_Truck_transition_from_mining():
  run = components.MiningRun()
  run.inbound_travel_time = 11
  truck = components.Truck(run)
  truck.remaining_time = 0
  truck.transition_from_mining()

  assert truck.state == components.TruckStatus.TRAVELING_TO_STATION
  assert truck.remaining_time == 11

def test_Truck_transition_from_inbound_to_unloading():
  run = components.MiningRun()
  run.inbound_travel_time = 11
  run.unloading_time = 12
  truck = components.Truck(run)
  truck.remaining_time = 0
  station = components.Station(run)
  station.state = components.StationStatus.IDLE
  stations = [station]

  truck.transition_from_inbound(stations)

  assert truck.state == components.TruckStatus.UNLOADING
  assert truck.remaining_time == 12

def test_Truck_transition_from_inbound_to_idle():
  run = components.MiningRun()
  run.idle_wait_time = 9
  run.inbound_travel_time = 11
  run.unloading_time = 12
  truck = components.Truck(run)
  truck.remaining_time = 0
  station = components.Station(run)
  station.state = components.StationStatus.BUSY
  stations = [station]

  truck.transition_from_inbound(stations)

  assert truck.state == components.TruckStatus.IDLE
  assert truck.remaining_time == 9

def test_Truck_transition_from_unloading():
  run = components.MiningRun()
  run.unloading_time = 12
  run.outbound_travel_time = 13
  truck = components.Truck(run)
  truck.remaining_time = 0
  truck.transition_from_unloading()

  assert truck.state == components.TruckStatus.TRAVELING_TO_MINE
  assert truck.remaining_time == 13

# Not writing unit test for Truck.cycle.
# All it is is a match/case statement that redirects to other functions that are unit tested.

def test_Truck_generate_report():
  run = components.MiningRun(run_hours=1)
  truck = components.Truck(run)
  truck.time_logs['MINING'] = 60

  expected = ('Status report for truck: unnamed\n'
              'Time spent mining. Total: 1 hours. Percent: 100\n'
              'Loads of Ore delivered: 0\n'
             )
  assert truck.generate_report() == expected

def test_Station():
  run = components.MiningRun()
  station = components.Station(run)

  expected = ('Station Name: unnamed\n'
              'Station status: StationStatus.IDLE\n\n'
              "Total Time in state: BUSY:0 IDLE:0\n"
            )
  assert f'{station}' == expected

def test_Station_attach():
  run = components.MiningRun()
  station = components.Station(run)
  truck = components.Truck(run)

  station.attach(truck)

  assert station.state == components.StationStatus.BUSY
  assert station.attached_truck == truck

def test_Station_release():
  run = components.MiningRun()
  station = components.Station(run)

  station.release()

  assert station.state == components.StationStatus.IDLE
  assert station.completed_loads == 1

def test_Station_generate_report():
  run = components.MiningRun(run_hours=1)
  station = components.Station(run)
  station.busy_minutes = 60

  expected = ('Status report for station: unnamed\n'
              'Time spent unloading. Total: 1 hours. Percent: 100\n'
              'Loads of Ore unloaded: 0\n'
             )
  assert station.generate_report() == expected

def test_Station_cycle_from_busy():
  run = components.MiningRun()
  station = components.Station(run)
  station.state = components.StationStatus.BUSY

  station.cycle()
  assert station.state == components.StationStatus.IDLE

def test_Station_cycle_from_idle():
  run = components.MiningRun()
  station = components.Station(run)
  station.state = components.StationStatus.IDLE

  station.cycle()
  assert station.state == components.StationStatus.IDLE
