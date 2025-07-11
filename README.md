# moonmoleltd2
Quick and dirty UI wrapper around moon mining exercise for Vast.

Nothing more than some hacked together flask boilerplate, with controls to define different simulation patterns for the moon miner.

Usage:

Download somewhere.

Probably need python, numpy, pandas, and flask installed.

(pip3 install $name)

Then set an environment variable:

export FLASK_APP=frontend.py 

And launch flask:

flask run --debug --port=8000

Open http://127.0.0.1:8000

Enter parameters (or leave at defaults)

Then poke the 'submit' button.

Click the "Run a new simulation" link to run again with different parameters.
