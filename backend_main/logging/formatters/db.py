import logging

from backend_main.logging.formatters.multiline import MultilineFormatter


"""
Formatter for loggers in db utility.
"""
file_db_formatter = MultilineFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
stdout_db_formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
