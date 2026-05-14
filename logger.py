import logging.config

logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            "datefmt": "%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        }
    },
    "root": {"level": "WARNING", "handlers": ["console"]},
    "loggers": {
        "agent": {"level": "INFO", "handlers": ["console"], "propagate": False},
        "main": {"level": "INFO", "handlers": ["console"], "propagate": False},
    },
})
