import argparse
import logging

import asyncio

from midirouter.router import RouterApplication

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s (%(levelname)s) %(name)s: %(message)s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--config',
        help='Router config')

    parser.add_argument(
        '--list_ports',
        action='store_true',
        help='Show all midi in/out ports')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(RouterApplication().run(options=parser.parse_args())))
