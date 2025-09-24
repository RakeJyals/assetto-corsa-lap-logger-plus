# Assetto Corsa Lap Logger

A lap-logging app for [Assetto Corsa](https://www.assettocorsa.net/home-ac).

When active the app will record lap times for the current track-vehicle combination.

---

## App

### Usage / Notes

The app displays a custom in-game HUD when active.

For each track-vehicle combination, a log file will be generated at the location `assettocorsa/apps/python/laplogger/logs` and session information will be written to this log. Logs assume the naming format of `vehicle_name - track_name - tracK_layout`.

The header of the file identifies the session configuration, while the bulk of the file is dedicated to recording lap details. For example:

Filename: `bmw_z4_gt3 - ks_nurburgring - layout_gp_b`

```txt
car: bmw_z4_gt3
track: ks_nurburgring
config: layout_gp_b

{'time': 135776, 'invalidated': False, 'lap': 1, 'splits': [47536, 46472, 41768]}
{'time': 125238, 'invalidated': False, 'lap': 2, 'splits': [39054, 44658, 41526]}
```
Note that in this form, this data can be incorportated into a pandas dataframe using pd.DataFrame.from_records(data) where data is the list of rows of this file (minus the metadata)
> TODO: This log can then be visualised as a graph in order to inspect lap splits/times.

### Logging

There are two kinds of AC log commands available:

- `ac.log` which logs to `py_log.txt`. This persists after the session is ended.
- `ac.console` which logs to `log.txt` and is available via the console (Home key) in game. This persists only while running.

By default, console logs are located at `C:\User\My Documents\Assetto Corsa\logs`

![Image](/Documentation/20190518203937-HUD.jpg)

## Installation

In order to install:

- Merge the folder `assettocorsa` with the `assettocorsa` game folder. This will place the app script at the correct location.
- Ensure that the app is enabled in game.

Troubleshooting:

- Insect the logs should any issue occur (see **Logging** section)

## Credit

Thanks to [**assettocorsamods**](https://assettocorsamods.net) for:

- The link to **Giovanni Romagnoli's** [AC Python API documentation](https://assettocorsamods.net/threads/doc-python-doc.59/).
- A fantastic [onboarding tutorial](https://assettocorsamods.net/threads/getting-started-with-ac-app-developing.716/) to modding in AC.
