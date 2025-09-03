# ============================================================================
# constants.py - Centralized constants for LegalTTSV2

# This module defines project-wide constants for chunking, limits, and other
# configuration values that should be consistent across all modules.
# Currently only controls max chunk length but author intends this to be the hub for constants across the configuration.
# ============================================================================


MAX_CHUNK_LENGTH = 750

# User-editable constants for prompt template replacement
USER_CONSTANTS = {
	"Username": "Deponent",  # Change this value as needed
	# Add more user constants here
}
