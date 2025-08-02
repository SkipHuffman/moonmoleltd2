""" Quick and Crude mock up of a possible UI for Moon Mole LTD lunar mining simulation.
Do not judge this code as completed work!  It isn't even prototype quality!!
I literally slapped this together using tools I have never, rarely, or not in over a decade, used.

I think if I started adding ToDo comments here it would end up 60% by weight.
"""

import base64
from io import BytesIO
from dataclasses import dataclass
from flask import Flask, request, render_template, url_for, redirect
from matplotlib.figure import Figure
import pandas
from components import MiningRun
from simulate import simulation

app = Flask(__name__)
app.config['SECRET_KEY'] = '502B3992-78AF-4936-A185-92A8F579D8E3'


@dataclass
class RunReport(MiningRun):
  """ Set the parameters for a mining run, including defaults.
  """
  # pylint: disable=too-many-instance-attributes
  pd_data: pandas.DataFrame | None = None
  idle_wait_time = 5
  inbound_travel_time = 30
  outbound_travel_time = 30
  slice_time = 5
  unloading_time = 5
  columns_to_exclude = []
  report_as_percent = False
  truck_components = ['MINING', 'TRAVELING_TO_STATION', 'IDLE', 'UNLOADING', 'TRAVELING_TO_MINE']
  station_components = ['BUSY', 'IDLE.1']
  base_components = truck_components + station_components

  def __init__(self, r):
    super().__init__()
    self.max_trucks = 1000
    self.max_stations = 100
    self.max_hours = 1000
    self.num_trucks = min(max(int(r.form['num_trucks']), 0), self.max_trucks)
    self.num_stations = min(max(int(r.form['num_stations']), 0), self.max_stations)
    self.run_hours = min(max(int(r.form['run_hours']), 0), self.max_hours)
    self.min_mining_hours = int(r.form['min_mining_hours'])
    self.max_mining_hours = int(r.form['max_mining_hours'])
    self.unloading_time = int(r.form['unloading_time'])
    self.idle_wait_time = int(r.form['unloading_time'])
    self.inbound_travel_time = int(r.form['transit_time'])
    self.outbound_travel_time = int(r.form['transit_time'])
    self.report_as_percent = bool('report_as_percent' in r.form)
    self.columns_to_exclude = []

def populate_pandas_dataframe(run):
  """ Initialize and populate the pandas dataframe. Calculate percentates.
  """
  # pylint: disable=no-member
  run.pd_data = pandas.read_csv('mining_report.csv', sep=',', header=3, index_col=0)
  if run.report_as_percent:
    for component in run.truck_components:
      run.pd_data[component] = round(100*(run.pd_data[component] / run.num_trucks))
    for component in run.station_components:
      run.pd_data[component] = round(100*(run.pd_data[component] / run.num_stations))
  if run.columns_to_exclude:
    run.pd_data = run.pd_data.drop(columns=run.columns_to_exclude)
  run.pd_data.style.format(precision=0)

def get_plot(run, components, name):
  """ Generate the chart/plot as a png.
  """
  # pylint: disable=no-member
  fig = Figure()
  ax = fig.subplots()
  components = sorted(list(set(components) - set(run.columns_to_exclude)))
  ax.plot(run.pd_data[components])
  ax.legend(components, title='Efficiency', loc='center left', bbox_to_anchor=(1,0,0.50,1))
  ax.set(xlabel='Five minute slices', ylabel='Devices available, or Percent active',
        title=f'Moon Mole LDT simulation: {name} results')
  buf = BytesIO()
  fig.savefig(buf, format="png", bbox_inches='tight')
  return base64.b64encode(buf.getbuffer()).decode("ascii")

def define_base_report(run_report):
  """ Create the basic HTML form with the summary information only.
  """
  return ('<h1>Mining Simulation Report</h1><br>'
          f'Number of trucks: {run_report.num_trucks}<br>'
          f'Number of stations: {run_report.num_stations}<br>'
          f'Length of run in hours: {run_report.run_hours}<br>'
           '<hr>'
           'Total Truck Loads Collected:'
          f' <b>{run_report.total_load_count}</b><br>'
          f'Truck Efficiency: <b>{run_report.generate_truck_efficiency()}</b> (maximum <70)'
           ' measured as hours spent actively mining over the full run time.  <br>'
          f'Station Efficiency: <b>{run_report.generate_station_efficiency()}</b> measured as'
           ' hours spent actively unloading ore over the full run time.  <br>'
         )

@app.route('/create/', methods=('GET', 'POST'))
def create():
  """ Either render the form to define a simulation, or run it and print the results.
  """
  if request.method == 'POST':
    run = RunReport(request)
    checked_boxes = request.form.getlist('included_columns')
    for checkbox in run.base_components:
      if checkbox not in checked_boxes:
        run.columns_to_exclude.append(checkbox)
    run_report = simulation(run)
    populate_pandas_dataframe(run)
    printable_report = define_base_report(run_report)
    if run.truck_components:
      truck_plot = get_plot(run, run.truck_components, 'Mining Truck')
      printable_report +=  f"<img src='data:img/png;base64,{truck_plot}'/>"
    if run.station_components:
      station_plot = get_plot(run, run.station_components, 'Unloading Station')
      printable_report += f"<img src='data:img/png;base64,{station_plot}'/>"
    printable_report += '<hr><br><a href=.>Run a new simulation</a>'
    return printable_report

  return render_template('create.html')

@app.route("/")
def index():
  """ Just make sure the root entry point isn't blocked, because that looks extra stupid.
  """

  return redirect(url_for('create'))
