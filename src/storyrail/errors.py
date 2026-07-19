class StoryRailError(Exception):
    """Base class for expected StoryRail failures."""


class ScriptLoadError(StoryRailError):
    """Raised when a script file cannot be read or decoded."""


class ScriptValidationError(StoryRailError):
    """Raised when decoded script data violates schema rules."""
