import asyncio
import logging

import mido

from midirouter.routers.base import BaseRouter
from midirouter.device.display import Push2Display
from midirouter.routers.push2.pages.chord import Push2ChordPage

logger = logging.getLogger(__name__)


class Push2Router(BaseRouter):

    _display_connected = False
    _display_page = None
    _display = None

    async def run(self):
        self._display = Push2Display(
            on_connected=self.on_display_connected,
            on_disconnected=self.on_display_disconnected,
        )
        self._display_page = Push2ChordPage(
            self._in_device, on_midi_out=self.on_midi_out
        )
        self._display_page.initialize()

        await self._display.connect()
        logger.info("Running push2 router")

        await self.wait()

    def on_display_connected(self):
        """Callback when push 2 display is initialized"""
        self._display_connected = True
        asyncio.create_task(self.display_loop())

    def on_display_disconnected(self):
        """Callback when push 2 display is disconnected"""
        self._display_connected = False

    async def display_loop(self):
        while self._display_connected:
            frame = self._display_page.build()
            self._display.show(frame)

    def on_midi_out(self, message, notes):
        logger.info(f"{message.type} {notes}")
        for out_device in self._out_devices:
            for note in notes:
                out_device.send(
                    mido.Message(
                        type=message.type,
                        channel=message.channel,
                        note=note,
                        velocity=message.velocity,
                        time=message.time,
                    )
                )
