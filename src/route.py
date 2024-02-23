import os
import json
import argparse
import logging

import asyncio

from midirouter.device.general import GeneralMidiDevice
from midirouter.device.push2 import Push2Device
from midirouter.routers.base import BaseRouter
from midirouter.routers.push2 import Push2Router
from midirouter.utils import get_in_ports, get_out_ports


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s (%(levelname)s) %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class RouterApplication:
    """Application entry point."""

    routers = None

    def create_device(self, name, pattern):
        device_class = {"general": GeneralMidiDevice, "push2": Push2Device}.get(
            name, GeneralMidiDevice
        )
        return device_class(pattern=pattern)

    def create_router(self, name, in_device, out_devices):
        router_class = {"base": BaseRouter, "push2": Push2Router}.get(name, BaseRouter)
        return router_class(in_device=in_device, out_devices=out_devices)

    async def run(self, options=None):

        if options.list_ports:
            logger.info("List of input ports {}".format(get_in_ports()))
            logger.info("List of output ports {}".format(get_out_ports()))
            return

        # read config file
        self.routers = {}
        current_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = f"{current_dir}/midirouter/data/{options.config}"
        with open(config_file) as f:
            config = json.loads(f.read())

        in_device = self.create_device(config["in"].pop("name"), config.get("pattern"))

        out_devices = [
            self.create_device(device_conf.pop("name"), device_conf.get("pattern"))
            for device_conf in config["out"]
        ]

        router = self.create_router(config["router"], in_device, out_devices)
        await router.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", help="Router config")

    parser.add_argument(
        "--list_ports", action="store_true", help="Show all midi in/out ports"
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        asyncio.gather(RouterApplication().run(options=parser.parse_args()))
    )
