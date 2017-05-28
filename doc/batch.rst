Batch plot creation
===================

It is possible to create the plots using a command-line tool.

Examples:

.. code-block :: bash

    # All data (per month)
    ./batch.py plot1.png                              

.. image :: example.png

.. code-block :: bash

    # December data (per hour)
    ./batch.py --x=hour --month=12 plot2.png         
    
.. image :: plot2.png

.. code-block :: bash

    # December data (per hour), in the altitude range 200 to 300 m
    ./batch.py --altitude=200,300 --x=hour --month=12 plot3.png     
    
.. image :: plot3.png   

.. code-block :: bash

    # All data for sensor with id vsstastr
    ./batch.py --id=vsstastr --x=hour  plot4.png     
    
.. image :: plot4.png   