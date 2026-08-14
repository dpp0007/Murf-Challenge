"""
Logging compatibility patch for LiveKit.

MUST be imported FIRST, before any other imports.
Patches logging.Logger to add trace() method that doesn't exist in stdlib.

LiveKit's audio_recognition module calls logger.trace() which causes:
  AttributeError: 'Logger' object has no attribute 'trace'

This module fixes it by adding trace() as a method on logging.Logger.
"""

import logging

# Patch logging.Logger class BEFORE any loggers are created
if not hasattr(logging.Logger, 'trace'):
    def _trace(self, message, *args, **kwargs):
        """Add trace() method to Logger - delegates to DEBUG level"""
        if self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, message, args, **kwargs)
    
    # Add to class
    logging.Logger.trace = _trace
    
    # Also add to root logger
    if not hasattr(logging.root, 'trace'):
        logging.root.trace = lambda msg, *args, **kwargs: logging.root.debug(msg, *args, **kwargs)
