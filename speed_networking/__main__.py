import os
import argparse

import logging
# logging.basicConfig(level=logging.DEBUG)

from .bot import Bot


def main():
    parser = argparse.ArgumentParser(
        prog="speed-networking",
        description="Slack Bot for speed networking random meetings"
    )
    args = parser.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN")
    secret = os.environ.get("SLACK_SIGNING_SECRET")
    bot = Bot(token=token)
    # TODO: add port as parameter
    bot.start(8081)


if __name__ == "__main__":
    main()
