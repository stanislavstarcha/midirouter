import logging
import time

import mido

logger = logging.getLogger(__name__)


class MidiEvents:

    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    PITCHWEEL = "pitchwheel"


def _find_port(names, port_pattern=None):

    logger.info("Looking for %s in %s", port_pattern, names)
    if not names or not port_pattern:
        logger.warning("No midi devices or pattern empty")
        return None

    for name in names:
        if port_pattern in name:
            return name


class MidiIn:

    _port = None

    def __init__(self, port_pattern=None, required=False):
        if not port_pattern:
            logger.warning("No input port specified")
            return

        logger.info("Creating MIDI IN for %s", port_pattern)
        port_name = None
        while not port_name:
            port_name = _find_port(self.get_port_names(), port_pattern)
            if port_name or (not port_name and not required):
                break
            logger.warning("In MIDI port for %s not found. Waiting...", port_pattern)
            time.sleep(5)

        if port_name:
            logger.info(f"Found MIDI IN port {port_name}")
            self._port = mido.open_input(port_name)
            logger.info("MIDI IN port %s opened", port_name)

    def get_port_names(self):
        return mido.get_input_names()

    def set_callback(self, callback):
        if self._port:
            self._port.callback = callback


class MidiOut:

    _port = None
    _channel = None

    def __init__(self, channel=None, port_pattern=None, required=False):
        logger.info("Creating MIDI OUT for %s", port_pattern)
        self._channel = channel

        if not port_pattern:
            return

        port_name = None
        while not port_name:
            port_name = _find_port(self.get_port_names(), port_pattern)
            if port_name or (not port_name and not required):
                break
            logger.warning("Out MIDI port for %s not found. Waiting...", port_pattern)
            time.sleep(5)

        if port_name:
            self._port = mido.open_output(port_name)
            logger.info("MIDI OUT port %s opened", port_name)

    def send(self, message):

        if not self._port:
            return

        if self._channel:
            message.channel = self._channel
        self._port.send(message)

    def get_port_names(self):
        return mido.get_output_names()

    def clock(self):
        self._port.send(mido.Message("clock"))
