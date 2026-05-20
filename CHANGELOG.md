# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024

### Added
- Complete code refactoring with improved structure
- Comprehensive logging throughout all services
- Type hints for better code clarity
- Detailed docstrings for all classes and methods
- Constants extracted from magic numbers
- Improved error handling and recovery
- Better separation of concerns

### Changed
- Replaced print statements with proper logging
- Improved configuration management with better validation
- Enhanced audio output with proper resource cleanup
- Better VAD segmentation with clearer logic
- Refactored LLM streaming with improved error handling
- Updated STT service with better error messages
- Improved TTS service with validation

### Removed
- Unused test files (test.py, voice_bot_v2.py, voice_bot_v3.py)
- Old voice_bot.py in root directory
- Unused dependencies from requirements.txt

### Fixed
- Proper cleanup on application shutdown
- Better handling of empty audio segments
- Improved timeout handling for API requests
- Fixed potential resource leaks in audio streams

## [0.1.0] - Initial Release

### Added
- Basic voice bot functionality
- Deepgram STT integration
- OpenRouter LLM integration
- Edge TTS integration
- Voice Activity Detection
