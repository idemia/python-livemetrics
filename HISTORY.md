
Release History
===============

0.8 (2025-11-01)
----------------

- Support Python 3.10 to 3.14
- Django 4.2.x and 5.2.x.
- Flask 3.1.x

0.7.1 (2024-05-17)
------------------

- Support Python up to version 3.12
- Upgrade COTS
- Use github workflow
- Increase robustness and reponsiveness of the dashboard

0.6 (2020-07-03)
----------------

- Fix display of dashboard when there is a lot of gauges
- support of TLS monitored app in dashboard

0.5 (2020-04-12)
----------------

- fix: update memory metric to include text+data+stack
- dashboard: operator min & max - precision for values
- Dashboard: support list of servers (i.e. list of values) with operator sum and average

0.4 (2020-03-22)
----------------

- Add support for Python 3.8
- Add children user time in cpu metric
- Add metric ``num_threads``

0.3 (2019-09-09)
----------------

- Rework of the dashboard to separate value and display (new format for the description file)
- Make the dashboard configuration file a Jinja2 file (to be able to define variables, macros, etc.)
- Fix memory gauge on recent Linux

0.2 (2019-07-24)
----------------

- Evolution of the dashboard
- Addition of an automatic gauge for cpu and memory (Linux only)

0.1 (2019-07-09)
----------------

- Initial release
