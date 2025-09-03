
# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased/Ideas]
- Refine hardcoded AI prompts to ensure speakers don't switch so often.
- Refine audio de-duplication to check 'repeat zones' for audio issues and more aggressively pare back
- Dockerize application - Higgs(once more of the list has been completed)
- Further post-processing with whisper/ffmpeg and/or secondary checking of audio files by LLMs. Identify pieces of audio which  illegible and re-process with Orpheus and insert back into main audio file. Also comparing the original text to the whisper log file to determine where there are segments of missing text, then rerecording these and inserting them back into the audio. - Higgs
- Better handling of legal terms such as 'precedent' - find ways to ensure these are read properly by the model.
- Prompt library - support for different types of Australian legal judgments: ensure judge names are read properly, process text and AI inputs based on standard documentation style of major courts, etc. Better utilise emotion tags from Orpheus, maybe have derpy dan summarise the case academically, then break it down with jokes and bad comparisons while laughing and sighing
- Support for Austlii - older cases don't have .rtf conversions and are all stored in plain text. I'd like to just link an Austlii page and have a crawler grab and format the text before using the audio conversion pipeline. Could integrate directly with the database so that the user could just put in a case citation. - SKK
- Post-processing of LLM summaries for accuracy - use a different model to web search for published summaries and compare for accuracy, perhaps grant an accuracy rating and send for regeneration with further context if accuracy is below a certain threshhold
- File support and compatibility - make gradio only accept supported file types.
- Tempo/prosody control - slow down audio for emphasis when quoting passages or reading headings
- Add factual background for summaries and case readings when a looking at appeal documents
- Chapterised audio and audio tagging
- Support for legislation and bills
- Leverage jade/fedleg/vicleg APIs to generate audio summaries of new rulings as audio 'legal news' segments
- Utilise/improve regex doc handling to ensure quality outcomes from low-end local MLMs.

# [1.2.3]
### Added
- Added user constant "Time" to USER_CONSTANTS in `Core/constants.py`, which provides the current system time.
- Added user constant "Greeting" to USER_CONSTANTS in `Core/constants.py`, which dynamically generates "Good morning/afternoon/evening {Username}" based on the user's local time and Git username.

## [1.2.2] - 2025-09-03
### Added
- Support for user constants in prompt templates: you can now use tags like `{Username}` in any prompt, which will be replaced with values from the `USER_CONSTANTS` dictionary in `Core/constants.py`.

## [1.2.1] - 2025-09-03
### Added
- Dynamic prompt template dropdown: now lists all .txt files in the Prompts directory automatically.
- Improved .gitignore handling: only keeps core prompt templates in version control, ignores others.
### Changed
- Chunk-by-chunk log output now shows chunk number and character count instead of a text preview.

## [1.2.0] - 2025-09-03
### Added
- Support for custom prompts: users can now enter any prompt directly in the prompt textbox.
- Prompt templates from the prompt library are loaded into the textbox as editable templates.
- Users can freely tweak prompt templates before processing.
- The system always uses the current textbox value as the prompt for processing.

### [1.1.2] - 2025-09-02
### Added
- Updated UI with support for custom colours (red-on-black theme, minimal CSS overrides, and Gradio theming).
- Added support for .txt files.

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
