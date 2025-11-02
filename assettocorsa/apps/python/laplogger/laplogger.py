import sys
import ac
import acsys

import os, platform
from datetime import datetime
from time import sleep

if platform.architecture()[0] == "64bit":
	sysdir = os.path.dirname(__file__)+'/stdlib64'
else:
	sysdir = os.path.dirname(__file__)+'/stdlib'

sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";."

from loggerlibs.sim_info import info

'''
WARNING: Current way of writing to files breaks when using "Return to Garage" function in AC
'''
# TODO: Fix above

# -----------------------------------------
# Constants
# -----------------------------------------

# The name of the custom HUD window displayed when this app is active.
APP_NAME = "Lap Logger"
# Because the script is run from the context of the main .exe we need to point to provide a relative path to this script.
LOG_DIR = "apps/python/laplogger/logs"
# TODO: config file with desired log path


# -----------------------------------------
# Variables
# -----------------------------------------

active = False

appWindow = None
logFile = None

lblLapCount = None
lblBestLap = None
lblLastLap = None
lblCurrentTime = None

lapCount = 0
bestLap = 0
lastLap = 0

lastLapInvalidated = False

# -----------------------------------------
# Asseto Corsa Events
# -----------------------------------------

def acMain(ac_version):

	log("Starting {}".format(APP_NAME))

	# Setting up app window
	global appWindow
	appWindow = ac.newApp(APP_NAME)
	ac.setSize(appWindow, 150, 200)
	log("Initialized App Window")
	# This was commented out when I forked this project, but this would just activate the app handlers at the bottom which
	# only send console logs and toggle the "active" variable, which is unused
	#ac.addOnAppActivatedListener(appWindow, onAppActivated)
	#ac.addOnAppDismissedListener(appWindow, onAppDismissed)

	# Display labels
	global lblLapCount
	lblLapCount = ac.addLabel(appWindow, "")
	ac.setPosition(lblLapCount, 3, 30)

	global lblBestLap
	lblBestLap = ac.addLabel(appWindow, "")
	ac.setPosition(lblBestLap, 3, 60)

	global lblLastLap
	lblLastLap = ac.addLabel(appWindow, "")
	ac.setPosition(lblLastLap, 3, 90)

	global lblCurrentTime
	lblCurrentTime = ac.addLabel(appWindow, "")
	ac.setPosition(lblCurrentTime, 3, 120)

	global lastLapInvalidated_display
	lastLapInvalidated_display = ac.addLabel(appWindow, "")
	ac.setPosition(lastLapInvalidated_display, 3, 150)

	global off_track_display
	off_track_display = ac.addLabel(appWindow, "")
	ac.setPosition(off_track_display, 3, 180)

	# TODO: Save button
	'''
	save_button = ac.addButton(appWindow, "")
	ac.setPosition(save_button, 70, 30)
	ac.addOnClickedListener(save_button, openLog)
	'''

	openLog() # Opens log file to writing

	return APP_NAME


def acUpdate(deltaT):
	
	# if (not active):
		# return
	
	# Functions below are in house
	updateState()
	refreshUI()


def acShutdown():
	closeLog()  # Just closes file


# -----------------------------------------
# Helper Functions
# -----------------------------------------

def log(message, level = "INFO"):
	'''Logs a message to the py_log with the (optional) specified level tag.'''
	ac.log("laplogger [{}]: {}".format(level, message))


def getFormattedLapTime(lapTime):
	'''Returns a lap time string formatted for display.'''

	if (not lapTime > 0):
		return "--:--:--"

	minutes = int(lapTime/1000/60)
	seconds = int((lapTime/1000)%60)
	millis = lapTime - (int((lapTime/1000))*1000)

	return "{}:{:02d}:{:03d}".format(minutes, seconds, millis)


def updateState():
	'''Updates the state of all variables required for logging.'''

	global lastLapInvalidated

	# Not working, important to get fixed
	if ac.getCarState(0, acsys.CS.LapInvalidated) != 0:  # Tested value can be 0 or 1
		lastLapInvalidated = True

	
	# Record lap info if new lap is started
	global lapCount
	currentLap = ac.getCarState(0, acsys.CS.LapCount)
	if (lapCount < currentLap):  # TODO: Figure out why first response is 0
		lapCount = currentLap
		sleep(5)
		writeLogEntry()
		lastLapInvalidated = False


def refreshUI():
	'''Updates the state of the UI to reflect the latest data.'''

	global lblLapCount, lapCount
	ac.setText(lblLapCount, "Laps: {}".format(lapCount))

	global lblBestLap, bestLap
	bestLap = ac.getCarState(0, acsys.CS.BestLap)
	ac.setText(lblBestLap, "Best: {}".format(getFormattedLapTime(bestLap)))

	global lblLastLap, lastLap
	lastLap = ac.getCarState(0, acsys.CS.LastLap)
	ac.setText(lblLastLap, "Last: {}".format(getFormattedLapTime(lastLap)))

	global lblCurrentTime
	ac.setText(lblCurrentTime, "Time: {}".format(getFormattedLapTime(ac.getCarState(0, acsys.CS.LapTime))))

	global lastLapInvalidated_display, lastLapInvalidated
	ac.setText(lastLapInvalidated_display, "Lap Invalid {}".format(lastLapInvalidated))

	global off_track_display
	ac.setText(off_track_display, "Off Track {}".format(ac.getCarState(0, acsys.CS.LapInvalidated)))



# -----------------------------------------
# Logging
# -----------------------------------------

def openLog():  # Should be refactored to write log
	'''
	Opens log file, creating it if necessary
	'''
	log("Starting openLog")
	# Create a log name based on datetime (down to second) and driver
	LOG_NAME = "{}_{}.csv".format(str(datetime.now()).replace(" ", "_").replace(":", "-").split(".")[0], ac.getDriverName(0))


	if not os.path.exists(LOG_DIR):
		os.mkdir(LOG_DIR)

	shouldInit = not os.path.exists("{}/{}".format(LOG_DIR, LOG_NAME))
		
	global logFile
	logFile = open("{}/{}".format(LOG_DIR, LOG_NAME), "a+")

	# Set columns in csv, lap number is excluded because pandas uses it as index
	logFile.write("time,fuel,tire_wear1,tire_wear2,tire_wear3,tire_wear4\n")
	log("Completed openLog")

def writeLogEntry():  # TODO: Refactor to create string that can be piped into csv output
	'''Writes a new log entry to the log using the current state information.'''
	# TODO: Have all lap data be cached and write to file upon button press
	global logFile

	tire_wear = info.physics.tyreWear

	lapData = "{},{},{},{},{},{},{}".format(
		lapCount,
		ac.getCarState(0, acsys.CS.LastLap),
		round(info.physics.fuel, 2),
		round(tire_wear[0], 2),
		round(tire_wear[1], 2),
		round(tire_wear[2], 2),
		round(tire_wear[3], 2)
		# lastLapInvalidated
	)

	logFile.write("{}\n".format(lapData))


def closeLog():  # TODO: Deprecate
	global logFile
	logFile.close()

# -----------------------------------------
# Event Handlers
# -----------------------------------------

def onAppDismissed():
	ac.console("LapLogger Dismissed")
	active = False
	log("Dismissed")


def onAppActivated():
	ac.console("LapLogger Activated")
	active = True
	log("Activated")
