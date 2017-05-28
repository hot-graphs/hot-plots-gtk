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
of **4D histograms** along the following axes:

* year
* month
* hour (segmented 0:00-1:00, 1:00-2:00, ..., 23:00-0:00)
* temperature (segmented per 1 degree Celsius)

Each of the sensors is assigned a single JSON file with such
histogram.

The representation is based on the HistogramND class of the physt library
(see https://github.com/janpipek/physt ).

In addition to that, we keep a table of meta-data (in CSV format), describing various
sensor properties (augmented from the excel file):

* address
* GPS location
* altitude
* percentage of greenery in a surrounding circles of three different radii
* average year temperature
* diff of the average temperature from the overall sensor average

Conversion
----------

The raw CSV data can be converted to the JSON representation using
Python code:

.. code-block :: python

    from prepare import parse_data_file, create_histogram_files
    infile = "Bohunice.zip"
    outdir = "data"
    data = parse_data_file(infile)
    create_histogram_files(data, outdir)

or using a command-line tool:

.. code-block :: bash

    ./prepare.py ~/doc/projekty/BrnoHacks/teplarny/Slatina.zip data
    
**Note:** The conversion of meta-data is a less straight-forward.
To be documented later.

Module prepare
--------------

.. automodule:: prepare
    :members:
    :undoc-members:
    :show-inheritance:
