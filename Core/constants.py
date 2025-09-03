# ============================================================================
# constants.py - Centralized constants for LegalTTSV2

# This module defines project-wide constants for chunking, limits, and other
# configuration values that should be consistent across all modules.
# Currently only controls max chunk length but author intends this to be the hub for constants across the configuration.
# ============================================================================

import datetime
import subprocess

MAX_CHUNK_LENGTH = 750

# User-editable constants for prompt template replacement

def get_git_username():
	try:
		return subprocess.check_output(['git', 'config', 'user.name'], encoding='utf-8').strip()
	except Exception:
		return "Testing"

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
	"Username": get_git_username(),
	"Time": get_system_time(),
	"Greeting": None,  # Will be set below
	# Add more user constants here
}

# Set Greeting after Username is available
USER_CONSTANTS["Greeting"] = get_greeting(USER_CONSTANTS["Username"])
