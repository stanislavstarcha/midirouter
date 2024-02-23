import logging

from asyncio import Event

logger = logging.getLogger(__name__)


class BaseRouter:

    _in_device = None
    _out_devices = None

    def __init__(self, in_device, out_devices):
        self._in_device = in_device
        self._out_devices = out_devices

    async def run(self):
        self._in_device.add_callback(self.on_message)
        await self.wait()

    async def wait(self):
        await Event().wait()

    def on_message(self, message):
        if message.type != "clock":
            logger.info(message)
        for out_device in self._out_devices:
            out_device.send(message)
