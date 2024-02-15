import logging
from asyncio import Event

from midirouter.device import BaseDevice

logger = logging.getLogger(__name__)


class RouterApplication:
    """Application entry point."""

    # device to listen to
    in_device = None

    # device to route messages to
    out_device = None

    async def run(self, options=None):

        self.in_device = BaseDevice(
            in_port_pattern=options.in_port,
            required=True
        )

        self.out_device = BaseDevice(
            out_port_pattern=options.out_port,
            channel=options.out_channel,
            required=True
        )

        if options.list_ports:
            logger.info('List of input ports {}'.format(BaseDevice.get_input_port_names()))
            logger.info('List of output ports {}'.format(BaseDevice.get_output_port_names()))
            return

        if self.in_device.midi_in:
            self.in_device.midi_in.set_callback(self.route)
            await Event().wait()

    def route(self, message):
        logger.info('Sending message {}'.format(message))
        if self.out_device.midi_out:
            self.out_device.midi_out.send(message)
