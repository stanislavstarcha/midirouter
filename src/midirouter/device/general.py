import logging

import mido

from midirouter.utils import get_in_ports, get_out_ports

logger = logging.getLogger(__name__)


class GeneralMidiDevice:

    name = "general"

    # Predefined midi device name pattern
    PATTERN = None

    # Midi in port
    _in_port = None

    # Midi out port
    _out_port = None

    def __init__(self, pattern=None):
        pattern = pattern or self.PATTERN
        if pattern:
            port_name = self._find_port(get_in_ports(), pattern)
            if port_name:
                self._in_port = mido.open_input(port_name)
                logger.info(f"Opened IN port {port_name}")

            port_name = self._find_port(get_out_ports(), pattern)
            if port_name:
                self._out_port = mido.open_output(port_name)
                logger.info(f"Opened OUT port {port_name}")

        self.on_ready()

    def on_ready(self):
        pass

    def send(self, message):
        self._out_port.send(message)

    def set_callback(self, callback):
        if self._in_port:
            self._in_port.callback = callback

    @staticmethod
    def _find_port(names, pattern=None):
        logger.info("Looking for %s in %s", pattern, names)
        if not names or not pattern:
            logger.warning("No midi devices or pattern empty")
            return None

        for name in names:
            if pattern in name:
                return name
