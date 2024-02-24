import mido

from midirouter.device.general import GeneralMidiDevice


class MidiEvents:
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    PITCHWEEL = "pitchwheel"


class Push2Colors:

    BLACK = 0
    LIGHT_GRAY = 123
    DARK_GRAY = 124
    WHITE = 122

    BLUE = 125
    GREEN = 126
    RED = 127


class Push2Device(GeneralMidiDevice):

    name = "push2"
    PATTERN = "Push 2 Live Port"

    def on_ready(self):
        pass

    def highlight_pad(self, note, color=Push2Colors.WHITE):
        self._out_port.send(mido.Message(MidiEvents.NOTE_ON, note=note, velocity=color))

    def highlight_control(self, cc, color=Push2Colors.DARK_GRAY):
        self._out_port.send(
            mido.Message(MidiEvents.CONTROL_CHANGE, control=cc, value=color)
        )
