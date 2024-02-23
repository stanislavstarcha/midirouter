import logging
import time

import mido

from midirouter.utils import get_in_ports, get_out_ports

logger = logging.getLogger(__name__)


class GeneralMidiDevice:

    name = "general"

    # User defined midi device name pattern
    _pattern = None

    # Predefined midi device name pattern
    PATTERN = None

    # Midi in port
    _in_port = None

    # Midi out port
    _out_port = None

    _callbacks = None

    def __init__(self, pattern=None):
        self._pattern = pattern
        self._callbacks = []
        self.connect()
        self.on_ready()

    def connect(self):
        pattern = self._pattern or self.PATTERN
        if not pattern:
            return

        while True:
            port_name = self._find_port(get_in_ports(), pattern)
            if port_name:
                break
            logger.warning("In port not found, waiting...")
            time.sleep(5)

        self._in_port = mido.open_input(port_name)
        self._in_port.callback = self.on_midi_in
        logger.info(f"Opened IN port {port_name}")

        while True:
            port_name = self._find_port(get_out_ports(), pattern)
            if port_name:
                break
            logger.warning("Out port not found, waiting...")
            time.sleep(5)

        self._out_port = mido.open_output(port_name)
        logger.info(f"Opened OUT port {port_name}")

    def on_ready(self):
        pass

    def send(self, message):
        self._out_port.send(message)

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def on_midi_in(self, message):
        for callback in self._callbacks:
            callback(message)

    @staticmethod
    def _find_port(names, pattern=None):
        logger.info("Looking for %s in %s", pattern, names)
        if not names or not pattern:
            logger.warning("No midi devices or pattern empty")
            return None

        for name in names:
            if pattern in name:
                return name
