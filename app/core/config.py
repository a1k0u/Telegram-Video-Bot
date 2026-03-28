import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    def __init__(self) -> None:
        env_path = Path(__file__).resolve().parents[2] / ".env"

        if not env_path.exists():
            logger.error(".env file not found!")
            sys.exit(1)

        load_dotenv(env_path)

        if not os.getenv("BOT_TOKEN"):
            logger.error("Missing required env variable: BOT_TOKEN")
            sys.exit(1)

        self.BOT_TOKEN: str = os.getenv("BOT_TOKEN")

        channel_id = os.getenv("CHANNEL_ID")
        if not channel_id:
            logger.error("Missing required env variable: CHANNEL_ID")
            sys.exit(1)

        try:
            self.CHANNEL_ID: int | str = int(channel_id)
        except ValueError:
            self.CHANNEL_ID = channel_id

        self.WHITELIST_USER_IDS: set[int] = self._parse_user_id_list(os.getenv("WHITELIST_USER_IDS", ""))

    @staticmethod
    def _parse_user_id_list(raw: str) -> set[int]:
        ids: set[int] = set()
        for part in raw.split(","):
            part = part.strip()
            try:
                ids.add(int(part))
            except ValueError:
                logger.error(f"Invalid user id in WHITELIST_USER_IDS: {part!r}. Expected comma-separated integers.")
                sys.exit(1)
        return ids

    def is_user_allowed(self, user_id: int | None) -> bool:
        if not self.WHITELIST_USER_IDS:
            return True
        if user_id is None:
            return False
        return user_id in self.WHITELIST_USER_IDS

config = Config()
