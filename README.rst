TiimaWeb - Tiima Web Controller
===============================

This library can be used to control the Tiima web UI through a simple
Python API.  It uses MechanicalSoup for mimicing browser actions.

|PyPI|

.. |PyPI| image::
   https://img.shields.io/pypi/v/tiimaweb.svg
   :target: https://pypi.org/project/tiimaweb/


Installing
----------

TiimaWeb is in PyPI and can be installed simply by::

  pip install tiimaweb

or if you use Poetry::

  poetry add tiimaweb


Usage
-----

The library can be used from Python code like this:

.. code:: python

  from datetime import date, datetime

  import tiimaweb

  client = tiimaweb.Client()

  with client.login('username', 'password', 'company') as tiima:
      # Get all time blocks of 2020-02-29
      time_blocks = tiima.get_time_blocks_of_date(date(2020, 2, 29))

      # Print and delete all those time blocks
      for time_block in time_blocks:
          print(time_block)
          tiima.delete_time_block(time_block)

      # Add new time block
      tiima.add_time_block(
          start=datetime(2020, 3, 1, 8, 30),
          end=datetime(2020, 3, 1, 11, 45))
