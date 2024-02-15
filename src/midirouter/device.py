import logging

import mido

from midirouter.midi import MidiIn, MidiOut

logger = logging.getLogger(__name__)


class BaseDevice:
    """Base midi device."""

    midi_in = None
    midi_out = None

    IN_PORT_PATTERN = None
    OUT_PORT_PATTERN = None

    def __init__(self, in_port_pattern=None, out_port_pattern=None, channel=None, required=False):
        """Open in/out midi ports."""

        out_port_pattern = out_port_pattern or self.OUT_PORT_PATTERN
        if out_port_pattern:
            logger.info(f'Creating MIDI device on OUT PORT {out_port_pattern}')
            self.midi_out = MidiOut(
                required=required,
                channel=channel,
                port_pattern=out_port_pattern)

        in_port_pattern = in_port_pattern or self.IN_PORT_PATTERN
        if in_port_pattern:
            logger.info(f'Creating MIDI device on IN PORT {in_port_pattern}')
            self.midi_in = MidiIn(
                required=required,
                port_pattern=in_port_pattern)

    @classmethod
    def get_input_port_names(cls):
        return mido.get_input_names()

    @classmethod
    def get_output_port_names(cls):
        return mido.get_output_names()
