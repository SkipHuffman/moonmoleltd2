""" Unit tests for simulate core of moon mining simulator.
For portablity I have used only the most basic pytest functions.
No Mocks, or Magic, or fancy assert types. Only the most simple.
"""
# pylint: disable=missing-function-docstring,invalid-name


import simulate

def test_initialize_time_slice_report():
  expected = [['', 'Mining Truck', '', '', '', '', '', 'Unloading Station'],
              ['Slice Count', 'MINING', 'TRAVELING_TO_STATION', 'IDLE', 'UNLOADING',
                  'TRAVELING_TO_MINE', 'BUSY', 'IDLE']]

  detected = simulate.initialize_time_slice_report()
  assert detected == expected

def test_initialize_simulation_definition():
  simulate.ARGS = simulate.parse_args()
  expected = simulate.MiningRun(num_stations=1, num_trucks=1, run_hours=72, total_loads_collected=0, total_load_count=0,
                                total_idle_truck_time=0, total_busy_truck_time=0, total_idle_station_time=0,
                                total_busy_station_time=0, verbose_trucks=False, verbose_stations=False)
  detected = simulate.initialize_simulation_definition()
  assert detected == expected

def test_initialize_trucks_zero_trucks():
  sample_simulation_definition = simulate.MiningRun()
  expected = []
  detected = simulate.initialize_trucks(sample_simulation_definition)
  assert detected == expected

def test_initialize_trucks_one_truck():
  sample_simulation_definition = simulate.MiningRun(num_trucks=1)
  sample_truck = simulate.Truck(simulate.MiningRun(num_trucks=99))
  expected = [sample_truck]
  detected = simulate.initialize_trucks(sample_simulation_definition)
  # minimal test, really should use mocks.
  assert len(detected) == len(expected)
  # the sample truck definition is NOT the same as the default
  assert detected != expected

def test_initialize_unloading_stations_zero_stations():
  sample_simulation_definition = simulate.MiningRun()
  expected = []
  detected = simulate.initialize_unloading_stations(sample_simulation_definition)
  assert detected == expected

def test_initialize_unloading_stations_one_station():
  sample_simulation_definition = simulate.MiningRun(num_stations=1)
  sample_station = simulate.Station(simulate.MiningRun(num_stations=99))
  expected = [sample_station]
  detected = simulate.initialize_unloading_stations(sample_simulation_definition)
  # minimal test, really should use mocks.
  assert len(detected) == len(expected)
  # the sample truck definition is NOT the same as the default
  assert detected != expected

def test_summarize_truck_results():
  simulate.ARGS = simulate.parse_args()
  sample_simulation_definition = simulate.MiningRun()
  sample_truck = simulate.Truck(simulate.MiningRun())
  simulate.summarize_truck_results(sample_simulation_definition, [sample_truck])
  assert sample_simulation_definition.total_load_count == 0
  sample_truck.completed_loads = 1
  simulate.summarize_truck_results(sample_simulation_definition, [sample_truck])
  assert sample_simulation_definition.total_load_count == 1

# Not adding more summarize Test Results, because I should remove the goofy 'time_logs"

# Not adding test for 'generate final report' since it just generates a CSV file,
# and I need to figure out how to test that outside the google ecosystem.

def test_run_simulation():
  sample_simulation = simulate.MiningRun()
  sample_truck = simulate.Truck(sample_simulation)
  sample_station = simulate.Station(sample_simulation)
  detected =simulate.run_simulation(sample_simulation, [sample_station], [sample_truck])

  expected = [['', 'Mining Truck', '', '', '', '', '', 'Unloading Station'],
              ['Slice Count', 'MINING', 'TRAVELING_TO_STATION', 'IDLE',
               'UNLOADING', 'TRAVELING_TO_MINE', 'BUSY', 'IDLE']] 
  assert expected == detected


# ToDo, increase unit test coverage as project time permits
