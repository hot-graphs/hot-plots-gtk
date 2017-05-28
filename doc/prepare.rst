Data Preparation Tools
======================

Source data
-----------
The original data, obtained from the Brno municipality, are stored
in ZIPped CSV files, one file per city part.

* timestamp
* sensor id
* temperature value

All sensors are then described in an additional excel sheet. The information
contained includes:

* address (street + number)
* internal address
* city part
* GPS coordinates
* sensor type
* sensor IDs

Internal representation
-----------------------
The vast amount of individual temperature points is aggregated in the form
of 4D histograms along the following axes:

* year
* month
* hour (segmented 0:00-1:00, 1:00-2:00, ..., 23:00-0:00)
* temperature (segmented per 1 degree Celsius)

Each of the sensors is assigned a single JSON file with such
histogram.

In addition to that, we keep a table of meta-data (in CSV format), describing various
sensor properties:



Conversion
----------

.. code-block :: bash

    ./prepare.py -i *.zip -o data/


.. automodule:: prepare
    :members:
    :undoc-members:
    :show-inheritance:
