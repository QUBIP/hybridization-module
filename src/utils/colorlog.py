import logging
import datetime


#  Formatter for log file
class PlainFormatter(logging.Formatter):
    def format(self, record):
        indent = getattr(record, "indent", "")
        prefix = getattr(record, "prefix", "")
        state = getattr(record, "state", "")
        original_message = record.getMessage()
        _message = f"{indent}[{prefix}] [{state}] {original_message}"
        timestamp = self.formatTime(record, self.datefmt)
        return f"[{timestamp}] {_message}"


#  Formatter for console
class ColorFormatter(logging.Formatter):
    COLORS = {
        "KDFIX": "\033[94m",  # Blue
        "AGENT": "\033[95m",  # Magenta
        "QKD": "\033[96m",  # Cyan
        "PQC": "\033[93m",  # Yellow
        "INFO": "\033[90m",  # Gray
        "OK": "\033[92m",  # Green
        "KO": "\033[91m",  # Red
        "RESET": "\033[0m"  # Reset
    }

    def format(self, record):
        indent = getattr(record, "indent", "")
        prefix = getattr(record, "prefix", "")
        state = getattr(record, "state", "")
        original_message = record.getMessage()
        prefix_str = (f"{self.COLORS.get(prefix, self.COLORS['RESET'])}[{prefix}]{self.COLORS['RESET']}"
                      if prefix else "")
        state_str = (f"{self.COLORS.get(state, self.COLORS['RESET'])}[{state}]{self.COLORS['RESET']}"
                     if state else "")
        _message = f"{indent}{prefix_str} {state_str} {original_message}"
        timestamp = self.formatTime(record, self.datefmt)
        return f"[{timestamp}] {_message}"


# Filter for flagged console output
class ConsoleFilter(logging.Filter):
    def filter(self, record):
        return getattr(record, "to_console", False)


# Logger config
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# logs go to "hybrid.log" using the PlainFormatter.
file_handler = logging.FileHandler("hybrid.log", mode='a')
file_formatter = PlainFormatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# logs flagged with to_console=True
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.addFilter(ConsoleFilter())
console_formatter = ColorFormatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


def color_log(prefix, state, message, indent="", to_console=False):
    logger.info(message, extra={"prefix": prefix, "state": state, "indent": indent, "to_console": to_console})
