import logging
import os
import json

from functools import partial
from asyncio import Event

from midirouter.midi import MidiIn, MidiOut

logger = logging.getLogger(__name__)


class RouterApplication:
    """Application entry point."""

    routers = None

    async def run(self, options=None):

        if options.list_ports:
            logger.info("List of input ports {}".format(MidiIn.get_port_names()))
            logger.info("List of output ports {}".format(MidiOut.get_port_names()))
            return

        self.routers = {}
        current_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = f"{current_dir}/routes/{options.config}"
        with open(config_file) as f:
            config_file = json.loads(f.read())

        for router, mappings in config_file.items():
            self.routers[router] = {
                "in": MidiIn(port_pattern=mappings["in"], required=True),
                "out": [
                    MidiOut(
                        port_pattern=out_port,
                        required=True,
                    )
                    for out_port in mappings["out"]
                ],
            }

            self.routers[router]["in"].set_callback(partial(self.route, router))

        await Event().wait()

    def route(self, router, message):
        if message.type != "clock":
            logger.info(message)
        for out_device in self.routers[router]["out"]:
            out_device.send(message)
