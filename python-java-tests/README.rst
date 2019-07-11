
This directory contains some source code to evaluate this library against the dropwizard metrics Java library.

- Run the Java server (listening on port 8080)::

    cd java
    mvn clean install jetty:run

- Run the Python server (listening on port 7070)::

    cd python
    python pserver.py

  Pre-requisite: this library must be installed in the Python environment, Python 3.6 or higher must be used.

- Run the tests:

    python it.py

The tests will send the same events to the 2 servers and then compare the metrics published.
There is some tolerance in the comparison of the metrics.

Access the metrics from your browser::

    http://localhost:8080/metrics/meters/requests
    http://localhost:7070/monitoring/v1/metrics/meters
    http://localhost:7070/monitoring/v1/metrics/histograms

