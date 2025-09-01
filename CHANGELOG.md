# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased/Ideas]
- Refine hardcoded AI prompts to ensure speakers don't switch so often
- Refine audio de-duplication to check 'repeat zones' for audio issues and more aggressively pare back
- Dockerize application
- Further post-processing with whisper/ffmpeg and/or secondary checking of audio files by LLMs. Identify pieces of audio which  illegible and re-process with Orpheus and insert back into main audio file. Also comparing the original text to the whisper log file to determine where there are segments of missing text, then rerecording these and inserting them back into the audio.
- Better handling of legal terms such as 'precedent' - find ways to ensure these are read properly by the model.
- Prompt library - support for different types of Australian legal judgments: ensure judge names are read properly, process text and AI inputs based on standard documentation style of major courts, etc. Better utilise emotion tags from Orpheus, maybe have derpy dan summarise the case academically, then break it down with jokes and bad comparisons while laughing and sighing
- Support for Austlii - older cases don't have .rtf conversions and are all stored in plain text. I'd like to just link an Austlii page and have a crawler grab and format the text before using the audio conversion pipeline.
- Post-processing of LLM summaries for accuracy - use a different model to web search for published summaries and compare for accuracy, perhaps grant an accuracy rating and send for regeneration if accuracy is below a certain threshhold
- File support and compatibility - make gradio only accept supported file types. Add support for .txt


### [1.1.1] - 01/09/2025
## Changed
- Custom prompt logic now always uses the textbox as prompt text (never as a file path)
- UI label for custom prompt updated for clarity and consistency
- Updates to changelog with development ideas.

## Fixed
- Fixed bug where custom prompts would always take from an existing prompt file instead of the textbox

### [1.1.0] - 01/09/2025
## Added
- Initial changelog template for tracking improvements, features, and fixes.
- Support for Gradio UI
- Support for custom prompts in gui
- Support for non-hardcoded models in Ollama

### Changed
- Refactored doc_utils to include functions from pdf/docx/file conversion handlers.


### Removed
- Deprecation of tk gui

## [1.0.0] - 31-08-2025
### Added
- Initial release of LegalTTSV2.
