import argparse
import logging

import asyncio

from midirouter.mpd import MPDApplication

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s (%(levelname)s) %(name)s: %(message)s"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", help="Router config")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(MPDApplication().run(options=parser.parse_args()))
