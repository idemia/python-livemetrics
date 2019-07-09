
``livemetrics`` Library
=======================

A Python library for building and publishing live business metrics used to have insights
about the behavior of applications.

It is based on the Dropwizard `metrics <https://metrics.dropwizard.io/>`_ library for Java.

Release v\ |version|.

.. only:: html

    .. image:: https://img.shields.io/pypi/l/livemetrics.svg
        :target: https://pypi.org/project/livemetrics/
        :alt: CeCILL-C

    .. image:: https://img.shields.io/pypi/pyversions/livemetrics.svg
        :target: https://pypi.org/project/livemetrics/
        :alt: Python 3.x


Installation
------------

``livemetrics`` is published on PyPI and can be installed from there::

    pip install -U livemetrics

To install additional publishers, specify the optional dependency you need. For example::

    pip install -U livemetrics[aiohttp]

Getting Started
---------------

Create a :py:class:`livemetrics.LiveMetrics` instance as a global variable:

.. code-block:: Python

    LM = livemetrics.LiveMetrics(version,about,is_healthy,is_ready)

Then use it to record events or register values:

.. code-block:: Python

    LM.mark('event', 'result')
    LM.histogram('name', 100)

Access the metrics when needed with:

.. code-block:: Python

    LM.get_metrics('event','result')
    LM.get_histograms('name')

Or use one of the provided publishers.

API
---

.. toctree::

    modules
