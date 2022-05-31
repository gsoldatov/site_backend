import logging


class MultilineFormatter(logging.Formatter):
    """
    Class with overriden `format` method, which produces separate LogRecord instances for each 
    line of message and error text & stack, formats them separately and merges the resulting text lines.
    """
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
            ext_text_lines = record.exc_text.split("\n")
            lines.extend(ext_text_lines)
        if record.stack_info:
            stack_info_lines = self.formatStack(record.stack_info).split("\n")
            lines.extend(stack_info_lines)
        
        # Get a separate record for each line
        records_text = []
        for line in lines:
            # Replace separator char
            msg = line.replace(";", ",")

            # Pass existing record params, except for `exc_info`, which was processed into `lines` items earlier
            line_record = logging.LogRecord(record.name, record.levelno, record.pathname, record.lineno,
                msg, record.args, None, record.funcName, record.stack_info)
            line_record.__dict__ = record.__dict__  # pass `extra` dict to new records
            
            records_text.append(super().format(line_record))
        
        # Return merged texts of line records
        return "\n".join(records_text)
