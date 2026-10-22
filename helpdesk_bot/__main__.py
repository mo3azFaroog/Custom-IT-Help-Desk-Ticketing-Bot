"""Entry point: ``python -m helpdesk_bot``."""

import logging

from .bot import HelpDeskBot
from .config import load_config


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    config = load_config()
    HelpDeskBot(config).run(config.token, log_handler=None)


if __name__ == "__main__":
    main()
