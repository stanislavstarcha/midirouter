import logging

import mido

from midirouter.midi import MidiIn, MidiOut

logger = logging.getLogger(__name__)


class BaseDevice:
    """Base midi device."""

    midi_in = None
    midi_out = None

    IN_PORT_PATTERNS = None
    OUT_PORT_PATTERNS = None

    def __init__(self, in_port_patterns=None, out_port_patterns=None, channel=None, required=False):
        """Open in/out midi ports."""

        logger.info('Creating MIDI device')
        if self.OUT_PORT_PATTERNS or out_port_patterns:
            self.midi_out = MidiOut(
                required=required,
                channel=channel,
                port_patterns=self.OUT_PORT_PATTERNS or out_port_patterns)

        if self.IN_PORT_PATTERNS or in_port_patterns:
            self.midi_in = MidiIn(
                required=required,
                port_patterns=self.IN_PORT_PATTERNS or in_port_patterns)

    @classmethod
    def get_input_port_names(cls):
        return mido.get_input_names()

    @classmethod
    def get_output_port_names(cls):
        return mido.get_output_names()
