# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased/Ideas]
- Refine hardcoded AI prompts to ensure speakers don't switch so often
- Refine audio de-duplication to check 'repeat zones' for audio issues and more aggressively pare back
- Dockerize application
- Further post-processing with whisper/ffmpeg and/or secondary checking of audio files by LLMs. Identify pieces of audio which illegible and re-process with Orpheus and insert back into main audio file.
- Better handling of legal terms such as 'precedent' - find ways to ensure these are read properly by the model.

### [1.1.0] - 01/09/2025
## Added
- Initial changelog template for tracking improvements, features, and fixes.
- Support for Gradio UI
- Support for custom prompts in gui
- Support for non-hardcoded models in Ollama

### Changed
- Refactored doc_utils to include functions from pdf/docx/file conversion handlers.

### Fixed
- 

### Removed
- Deprecation of tk gui

## [1.0.0] - 31-08-2025
### Added
- Initial release of LegalTTSV2.
