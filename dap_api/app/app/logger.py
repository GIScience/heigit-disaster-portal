import functools
import logging
from logging.config import dictConfig
from pathlib import Path
import yaml

from app.config import settings

path = Path(__file__).parent.absolute()

with open(f'{path}/../log_config.yml', 'r') as stream:
    config = yaml.load(stream, Loader=yaml.FullLoader)

dictConfig(config)
logger = logging.getLogger(f'dap.app{"" if not settings.DEBUG else ".debug"}')

VERBOSE_LEVELS = ['debug', 'error', 'warn', 'warning']


def log(level: str = 'info'):
    """
    Function decorator to add log entries before and after function call.
    Takes log level strings as level argument.
    @param level: log level of the log entries
    @return: decorator function
    """
    def decorator_log(func):
        @functools.wraps(func)
        def wrapper_log(*args, **kwargs):
            # get logging function of specified level from logger
            level_log = getattr(logger, level)
            msg_start = f"Calling {func.__name__}"
            verbose = level in VERBOSE_LEVELS
            if verbose:
                args_repr = [repr(a) for a in args]
                kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
                signature = ", ".join(args_repr + kwargs_repr)
                msg_start += f"({signature})"
            level_log(msg_start)
            result = func(*args, **kwargs)
            level_log(f"Finished {func.__name__}{'' if not verbose else f'. Returned {result!r}'}")
            return result

        return wrapper_log

    return decorator_log


if __name__ == '__main__':
    import sys
    sys.argv
