import sys
import ac
import acsys

import os, platform, json
from datetime import datetime


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

# Load config file (TODO have default config and custom config for better integration with github - script crashes when trying to run os.path.exists here?)
# Because the script is run from the context of the main .exe we need to point to provide a relative path to this script.
with open("apps/python/laplogger/config.json", "r") as f:
	config = json.load(f)

LOG_DIR = config["log_path"]


# -----------------------------------------
# Variables
# -----------------------------------------

active = False

record_countdown = None
lapCount = 0
lastLap = 0

lastLapInvalidated = False
wasInPitlane = True
wasInPitBox = True

# -----------------------------------------
# Asseto Corsa Events
# -----------------------------------------

def acMain(ac_version):

	log("Starting {}".format(APP_NAME))

	# Setting up app window
	global appWindow
	appWindow = ac.newApp(APP_NAME)
	ac.setSize(appWindow, 175, 200)
	log("Initialized App Window")
	
	# This was commented out when I forked this project, but this would just activate the app handlers at the bottom which
	# only send console logs and toggle the "active" variable, which is unused
	# These listeners also seem to be nonfunctional TODO check other projects to see if they successfully integrate these
	#ac.addOnAppActivatedListener(appWindow, onAppActivated)
	#ac.addOnAppDismissedListener(appWindow, onAppDismissed)

	# Display labels
	global lblLapCount  # Now used for laps done in stint
	lblLapCount = ac.addLabel(appWindow, "")
	ac.setPosition(lblLapCount, 3, 30)

	global lblCurrentTime  # Now used for time in stint
	lblCurrentTime = ac.addLabel(appWindow, "")
	ac.setPosition(lblCurrentTime, 3, 60)

	global lblPitlaneTime
	lblPitlaneTime = ac.addLabel(appWindow, "")
	ac.setPosition(lblPitlaneTime, 3, 90)

	global testLabel1
	testLabel1 = ac.addLabel(appWindow, "")  # Is it right to initiate the variable here, compared to in the main?
	ac.setPosition(testLabel1, 3, 120)

	global testLabel2
	testLabel2 = ac.addLabel(appWindow, "")
	ac.setPosition(testLabel2, 3, 150)

	global testLabel3
	testLabel3 = ac.addLabel(appWindow, "")
	ac.setPosition(testLabel3, 3, 180)

	# TODO: Save button, check box for local or remote saving (or both), check box for auto save (choice should be persistent, so I'll need to create a config file)
	'''
	save_button = ac.addButton(appWindow, "")
	ac.setPosition(save_button, 70, 30)
	ac.addOnClickedListener(save_button, openLog)
	'''

	openLog() # Opens log file to writing

	return APP_NAME


def acUpdate(deltaT):
	# deltaT is in seconds!
	
	# if (not active):
		# return
	
	# Functions below are in house
	updateState(deltaT)
	refreshUI(deltaT)


def acShutdown():
	closeLog()  # Just closes file


# -----------------------------------------
# Helper Functions
# -----------------------------------------

def log(message, level = "INFO"):
	'''Logs a message to *py_log.txt* with the (optional) specified level tag.'''
	message = "laplogger [{}]: {}".format(level, message)
	ac.log(message)
	ac.console(message)


def getFormattedLapTime(lapTime, milis = True):
	'''Returns a lap time string formatted for display. lapTime is in miliseconds'''

	if (lapTime <= 0):
		return "--:--:--"

	minutes = int(lapTime/1000/60)
	seconds = int((lapTime/1000)%60)
	millis = lapTime - (int((lapTime/1000))*1000)

	return "{}:{:02d}:{:03d}".format(minutes, seconds, millis) if milis else "{}:{:02d}".format(minutes, seconds)


def updateState(deltaT):
	'''Updates the state of all variables required for logging.'''

	global lastLapInvalidated
	global record_countdown
	global lapCount

	# Not working, not important to get fixed
	if ac.getCarState(0, acsys.CS.LapInvalidated) != 0:  # Tested value can be 0 or 1
		lastLapInvalidated = True

	
	# Record lap info once enough time has passed for all memory to update
	if record_countdown:
		if record_countdown < deltaT:
			writeLogEntry()
			lastLapInvalidated = False
			record_countdown = None
		else:
			record_countdown -= deltaT

	# Update lap count and trigger any events that should occur on completion of lap, lapCount is used in hud and as lap id in log csv
	currentLap = ac.getCarState(0, acsys.CS.LapCount)
	if lapCount < currentLap:  # Check if player is on a new lap, then start countdown to log data if so
		lapCount = currentLap
		record_countdown = 3

	# TODO experiment with IsEngineLimiterOn (FYC?), NormalizedSplinePosition (position on track in 1d, [0,1] - is this one even useful?), 
	# WorldPosition (multi-dimensional coordiantes),
	# Can pass car id: isCarInPitlane, isCarInPit (pitbox), isConnected?
	# Can detect teleport to pits by noticing that InPitlane and InPit both switch to true at the same time

	# TODO check if car has entered/exited pitlane, teleported (inPitbox and inPitlane activate at the same time)



def refreshUI(deltaT):
	'''Updates the state of the UI to reflect the latest data.'''

	ac.setText(lblLapCount, "Laps (This Stint): {}".format(lapCount))  # TODO replace with laps in stint

	ac.setText(lblCurrentTime, "Time (This Stint): {}".format(  # TODO replace with time in stint
		getFormattedLapTime(ac.getCarState(0, acsys.CS.LapTime), milis=False)
	))

	# ac.setText(lblPitlaneTime, "Time in pitlane: {}".format(

	# ))
	
	global testLabel1
	ac.setText(testLabel1, "Current Time: {}".format(datetime.now().time()))

	global testLabel2
	ac.setText(testLabel2, "In pitlane: {}".format(ac.isCarInPitlane(0)))

	global testLabel3
	ac.setText(testLabel3, "In pitbox: {}".format(ac.isCarInPit(0)))

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

def writeLogEntry():  # TODO: Refactor to create string that can be piped into csv or JSON output
	'''Writes a new log entry to the log using the current state information.'''
	# TODO: Have all lap data be cached and write to file upon button press

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
	logFile.close()

# -----------------------------------------
# Event Handlers
# -----------------------------------------

def onAppDismissed():
	ac.console("LapLogger Dismissed")
	global active
	active = False
	log("Dismissed")


def onAppActivated():
	ac.console("LapLogger Activated")
	global active
	active = True
	log("Activated")
