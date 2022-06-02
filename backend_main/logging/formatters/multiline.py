import logging


class MultilineFormatter(logging.Formatter):
    """
    Records a separate record for each line in log `message`, `exc_info` and `stack_info`.
    Each line contains the same default and extra params and concatenated lines of `message`, `exc_info` and `stack_info`.
    Message is sanitized from containing log separator char.
    Extra params are sanitized from containing log separator and newline chars.
    """
    def __init__(self, fmt, separator = None, separator_replacement = None, *args, **kwargs):
        super().__init__(fmt, *args, **kwargs)
        self.separator = separator
        self.separator_replacement = separator_replacement
    
    def format(self, record):
        # Get message text and split in by new line characters
        lines = str(record.msg).split("\n")

        # Add text lines from exception text and stack trace
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            ext_text_lines = str(record.exc_text).split("\n")
            lines.extend(ext_text_lines)
        if record.stack_info:
            stack_info_lines = self.formatStack(record.stack_info).split("\n")
            lines.extend(stack_info_lines)
        
        # Get sanitized `extra` params
        extra = {k : self.sanitize(v) for k, v in record.__dict__.items() if k not in _default_log_record_params}
        
        # Get a separate record for each line
        records_text = []
        for line in lines:
            # Replace chars in msg
            msg = self.sanitize(line)

            # Pass existing record params, except for `exc_info` and `stack_info`, which was processed into `lines` items earlier
            line_record = logging.LogRecord(record.name, record.levelno, record.pathname, record.lineno,
                msg, record.args, None, record.funcName, None)
            line_record.__dict__.update(extra)  # pass `extra` params to new records
            
            records_text.append(super().format(line_record))
        
        # Return merged texts of line records
        return "\n".join(records_text)
    
    def sanitize(self, text):
        """ Replaces new line and separator chars in `text`. """
        text = str(text).replace("\n", " ")
        if self.separator:
            text = text.replace(self.separator, self.separator_replacement)
        return text


_default_log_record_params = set((k for k in logging.LogRecord(*[None] * 7).__dict__))