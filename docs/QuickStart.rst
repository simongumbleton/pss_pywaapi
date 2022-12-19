.. pss_pywaapi documentation master file, created by
   sphinx-quickstart on Wed Jun 17 18:43:53 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

QuickStart
=======================================

How to install and get started using the module. Further examples are included in the examples section.


Installation and Setup
===============
The module requires Python 3.6 or later.
If required, install the latest version of Python 3 from:
https://www.python.org/downloads/

Install the module via the pip command:

"pip install pss-pywaapi"

https://pypi.org/project/pss-pywaapi/


Getting Started
===============
To use the module, simply import as follows;

.. code-block:: python

   import pss_pywaapi



To connect to the Wwise authoring tool, call the connect() method. 

.. code-block:: python

   result = pss_pywaapi.connect()

This will initiate a connection to the wwise authoring tool on port 8095 by default. You can specify an alternative port by passing a value into connect() e.g.

.. code-block:: python

   result = pss_pywaapi.connect(8080)

If the connection is successful, then connect() will return a result structure containing useful information about the wwise connection, tool and project. If it fails, the return value will be bool False.

You may wish to include pretty print in your scripts if you want to print or log nicely formated structures such those returned by the Wwise Authoring API. e.g.

.. code-block:: python

   from pprint import pprint
   result = pss_pywaapi.connect()
   pprint(result)


Make sure to enable the Wwise Authoring API in the Wwise tool user preferences, and make sure to set the WAMP port to the value you want to use. For details see..
(https://www.audiokinetic.com/library/edge/?source=SDK&id=waapi.html)

