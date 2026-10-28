import logging

from bot import config
from bot.core.bot import CrowBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

def main():
    if not config.TOKEN:
        raise SystemExit("DISCORD_TOKEN missing. Put it in your .env file")
    CrowBot().run(config.TOKEN, log_handler=None)

if __name__ == "__main__":
    main()