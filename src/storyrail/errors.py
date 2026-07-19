class StoryRailError(Exception):
    """Base class for expected StoryRail failures."""


class ScriptLoadError(StoryRailError):
    """Raised when a script file cannot be read or decoded."""


class ScriptValidationError(StoryRailError):
    """Raised when decoded script data violates schema rules."""


class InvalidChoiceError(StoryRailError):
    """Raised when a choice index is not available on the current node."""


class GameFinishedError(StoryRailError):
    """Raised when a choice is attempted after reaching an ending."""


class ConfigurationError(StoryRailError):
    """Raised when AI provider environment settings are invalid."""


class ProviderError(StoryRailError):
    """Raised when an AI provider cannot produce narration."""
