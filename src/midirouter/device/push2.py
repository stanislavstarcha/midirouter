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
        self.highlight_pad(36, color=Push2Colors.BLACK)
        self.highlight_pad(37, color=Push2Colors.DARK_GRAY)
        self.highlight_pad(38, color=Push2Colors.LIGHT_GRAY)
        self.highlight_pad(39, color=Push2Colors.WHITE)

        self.highlight_pad(40, color=Push2Colors.BLUE)
        self.highlight_pad(41, color=Push2Colors.GREEN)
        self.highlight_pad(42, color=Push2Colors.RED)

        self.highlight_control(37, color=Push2Colors.WHITE)
        self.highlight_control(38, color=Push2Colors.WHITE)
        self.highlight_control(39, color=Push2Colors.WHITE)
        self.highlight_control(40, color=Push2Colors.WHITE)

        self.highlight_control(20, color=Push2Colors.WHITE)

    def highlight_pad(self, note, color=Push2Colors.WHITE):
        self._out_port.send(mido.Message(MidiEvents.NOTE_ON, note=note, velocity=color))

    def highlight_control(self, cc, color=Push2Colors.DARK_GRAY):
        self._out_port.send(
            mido.Message(MidiEvents.CONTROL_CHANGE, control=cc, value=color)
        )
