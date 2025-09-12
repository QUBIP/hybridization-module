import logging

import colorlog

from hybridization_module.model.config import LoggingConfiguration
from hybridization_module.model.shared_enums import LogType
from hybridization_module.model.shared_types import LogTypeInformation

_HM_LOG_COLORS = {
    "DEBUG" : "cyan",
    "INFO" : "green",
    "WARNING" : "yellow",
    "ERROR" : "red",
    "CRITICAL" : "bold_red"
}


def _get_logging_type_configuration(log_type: LogType) -> LogTypeInformation:
    """
    Extracts the type specific configuration from the LogType given in the logging configuration
    """
    if log_type == LogType.DEBUG:
        level = logging.DEBUG
    elif log_type == LogType.INFO:
        level = logging.INFO
    elif log_type == LogType.WARNING:
        level = logging.WARNING
    elif log_type == LogType.ERROR:
        level = logging.ERROR
    else:
        raise ValueError(f"Logging type {log_type} not implemented.")

    return LogTypeInformation(level=level)


def _setup_console_handler(log_type: LogType, no_color: bool) -> logging.Handler:
    console_handler = logging.StreamHandler()
    log_type_info = _get_logging_type_configuration(log_type)

    console_formatter = colorlog.ColoredFormatter(
        fmt="%(light_black)s%(asctime)s %(log_color)s[%(levelname)s] %(light_blue)s[%(threadName)s]%(reset)s: %(message)s",
        log_colors=_HM_LOG_COLORS,
        no_color=no_color,
    )

    console_handler.set_name("console")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_type_info.level)

    return console_handler


def _setup_file_handler(log_type: LogType, filename: str) -> logging.Handler:
    if filename == "":
        log_file_handler = logging.FileHandler("hybrid.log", mode="a")
    else:
        log_file_handler = logging.FileHandler(filename, mode="a")

    log_type_info = _get_logging_type_configuration(log_type)

    log_file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s",
    )

    log_file_handler.set_name("log_file")
    log_file_handler.setFormatter(log_file_formatter)
    log_file_handler.setLevel(log_type_info.level)

    return log_file_handler


def configure_logging(log_config: LoggingConfiguration) -> None:
    handlers = []

    ## Console logging
    if log_config.console_log_type != LogType.NONE:
        console_handler = _setup_console_handler(log_config.console_log_type, log_config.colorless_console_log)
        handlers.append(console_handler)

    ## File logging
    if log_config.file_log_type != LogType.NONE:
        log_file_handler = _setup_file_handler(log_config.file_log_type, log_config.filename)
        handlers.append(log_file_handler)

    logging.basicConfig(level=logging.DEBUG, handlers=handlers)