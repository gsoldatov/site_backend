import logging


"""
Formatter for loggers in db utility.
"""
file_db_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
stdout_db_formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
