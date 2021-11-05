# 2.0.1

* Bugfix: Fixes parsing errors due to diversly formatted date strings in the NeurOne protocol files.

# 2.0.0

* ⚠️  This release drops support for end-of-life python versions, most notably Python 2.7. It also
  introduces support for more recent python versions up to 3.9.
* Feature: `Recording`, `Session` and `Phase` objects now expose subject information read from the
  session protocol XML files as the `subject_info` property. This information is also exported to
  MNE objects.
* Feature: Conversion to MNE now sets the `meas_date` in the MNE `Info` object to the recording
  start date from the session protocol XML file.

# 1.1.7

* Bugfix: A crash could occur when trying to load a phase with no events.

# 1.1.6

* Bugfix: Reproducible ordering of sessions

  ⚠️  Session loading previously used `os.listdir` to find sessions. This function does not guarantee
  any specific order, which might lead to inconsistencies between systems or even runs on the same
  system. Sessions are now ordered chronological, i.e. according to their start time, which is
  probably what most users expect.

* Maintenance: Tests were migrated from Travis to GitHub Actions

# 1.1.5

* Github workflow for automatic deployment to PyPI

# 1.1.1

* Documentation updates for JOSS review

# 1.1.0

* New channel dropping feature
* Bugfixes for the export to python-mne

# 1.0.1

* Improved test stability
* Unified logging for all modules

# 1.0.0

* Initial release
