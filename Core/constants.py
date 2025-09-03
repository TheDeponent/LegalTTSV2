# ============================================================================
# constants.py - Centralized constants for LegalTTSV2

# This module defines project-wide constants for chunking, limits, and other
# configuration values that should be consistent across all modules.
# Currently only controls max chunk length but author intends this to be the hub for constants across the configuration.
# ============================================================================

import json
import urllib.request
import datetime
import subprocess
import os
import random
import time
import locale
try:
	import tzlocal
except ImportError:
	tzlocal = None
	
def get_state():
	try:
		with urllib.request.urlopen("https://ipinfo.io/json") as url:
			data = json.loads(url.read().decode())
			# 'region' is the state/region field in ipinfo.io's response
			return data.get("region", "Unknown")
	except Exception:
		return "Unknown"

MAX_CHUNK_LENGTH = 750

# User-editable constants for prompt template replacement

def get_git_username():
	try:
		return subprocess.check_output(['git', 'config', 'user.name'], encoding='utf-8').strip()
	except Exception:
		return "Testing"

def get_git_email():
	try:
		return subprocess.check_output(['git', 'config', 'user.email'], encoding='utf-8').strip()
	except Exception:
		return "unknown@example.com"

def get_short_time():
	return datetime.datetime.now().strftime('%H:%M')

def get_date():
	return datetime.datetime.now().strftime('%Y-%m-%d')

def get_day_of_week():
	return datetime.datetime.now().strftime('%A')

def get_timezone():
	if tzlocal:
		try:
			return tzlocal.get_localzone_name()
		except Exception:
			return "Unknown"
	return "Unknown"

def get_project_name():
	return os.path.basename(os.path.abspath(os.getcwd()))

def get_session_id():
	return str(int(time.time())) + str(random.randint(1000,9999))

def get_country():
	try:
		loc = locale.getdefaultlocale()
		if loc and len(loc) > 0 and loc[0]:
			return loc[0].split('_')[-1]
		else:
			return "Unknown"
	except Exception:
		return "Unknown"

def get_system_time():
	# Returns the current system time in a readable format
	return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_greeting(username):
	now = datetime.datetime.now().hour
	if 5 <= now < 12:
		part = "morning"
	elif 12 <= now < 18:
		part = "afternoon"
	else:
		part = "evening"
	return f"Good {part} {username}"


USER_CONSTANTS = {
	"State": get_state(),
	"Username": get_git_username(),
	"UserEmail": get_git_email(),
	"Time": get_system_time(),
	"ShortTime": get_short_time(),
	"Date": get_date(),
	"DayOfWeek": get_day_of_week(),
	"Timezone": get_timezone(),
	"ProjectName": get_project_name(),
	"SessionID": get_session_id(),
	"Country": get_country(),
	"Greeting": None,  # Will be set below
	# Add more user constants here
}

# Set Greeting after Username is available
USER_CONSTANTS["Greeting"] = get_greeting(USER_CONSTANTS["Username"])
