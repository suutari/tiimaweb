TiimaWeb Change Log
###################

0.3.2 - 2020-07-14
==================

* Fix reason code parsing


0.3.1 - 2020-03-15
==================

Changed
-------

* Check time block addition failures more carefully

Fixed
-----

* Fix automatic lunch prevention logic


0.3.0 - 2020-03-15
==================

Added
-----

* Add get_totals_list method for reading the work time calendar


0.2.0 - 2020-03-14
==================

Added
-----

* Add support for parsing TimeBlocks passing midnight
* Add CHANGELOG.rst file for keeping change log

Changed
-------

* Make compatible with Python 2.7

Fixed
-----

* Fix whitespace error in README


0.1.2 - 2020-03-06
==================

Changed
-------

* Enable syntax highlighting for the Python example in README


0.1.1 - 2020-03-06
==================

Added
-----

* Add PyPI link to README
* Add repository URL to package metadata
* Add LICENSE file with copyright information and MIT license

Changed
-------

* Do not require too so version of pytz


0.1.0 - 2020-03-06
==================

Added
-----

* Initial version of tiimaweb implementation
* Simple command line script named "tiimaweb"
* README file with usage example
* Code style configuration for flake8
* Type checking with mypy
* mypy-stubs for mechanicalsoup and bs4
* Package metadata to be used with Poetry
