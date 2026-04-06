"""
pleasant_loggers._levels

Adds a custom PERFORMANCE logging level (integer 15) to the stdlib logging
module. Extracted verbatim from utils.py with no functional changes.

Usage:
    from pleasant_loggers import add_performance_level

    add_performance_level()
    logger = logging.getLogger(__name__)
    logger.performance("step done", process_id="etl_1")
"""
import logging


PERFORMANCE_LEVEL_NUM: int = 15


def add_performance_level() -> None:
    """
    Register a custom PERFORMANCE log level (value 15, between DEBUG and INFO)
    on the stdlib logging module.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    logging.addLevelName(PERFORMANCE_LEVEL_NUM, "PERFORMANCE")

    def performance(self, message, *args, process_id: str = "", **kwargs):
        if self.isEnabledFor(PERFORMANCE_LEVEL_NUM):
            stacklevel = kwargs.pop("stacklevel", 1)
            if "extra" not in kwargs:
                kwargs["extra"] = {}
            kwargs["extra"]["process_id"] = process_id
            self._log(
                PERFORMANCE_LEVEL_NUM,
                message,
                args,
                stacklevel=stacklevel + 1,
                **kwargs,
            )

    logging.Logger.performance = performance
