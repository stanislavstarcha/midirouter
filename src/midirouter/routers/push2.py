import logging

import mido
from music_essentials import Note, Scale

logger = logging.getLogger(__name__)

from midirouter.routers.base import BaseRouter
from midirouter.device.push2 import Push2Colors


class Push2Router(BaseRouter):

    scale = {
        # notes in one octave
        "len": None,
        # all notes starting from C-1
        "notes": None,
    }

    modifiers = {
        0: False,
        1: False,
        2: False,
        3: False,
        4: False,
        5: False,
        6: False,
        7: False,
    }

    SCALES = {
        20: "major",
        21: "minor",
        22: "natural minor",
        23: "melodic minor",
        24: "dorian",
        25: "locrian",
        26: "lydian",
        27: "mixolydian",
        # "phrygian",
        # "major pentatonic",
        # "minor pentatonic",
    }

    async def run(self):
        self._in_device.set_callback(self.on_message)
        self.initialize_scales()
        self.initialize_pads()
        logger.info("Running push2 router")
        await self.wait()

    def initialize_scales(self):
        for i in range(8):
            self._in_device.highlight_control(20 + i)

    def initialize_pads(self):
        for i in range(36, 92):
            # self._in_device.highlight_pad(i, self.get_pad_default_color(i))
            self._in_device.highlight_pad(i, i - 35)

    def get_pad_default_color(self, note):
        color = Push2Colors.DARK_GRAY
        if (note - 36) % 8 == 0:
            color = Push2Colors.LIGHT_GRAY
        if (note - 32) % 8 == 0:
            color = Push2Colors.LIGHT_GRAY
        return color

    def modify(self, note_index):

        resolved = [self.scale["notes"][note_index]]

        # major triad
        if self.modifiers[0]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 2] - 1,
                self.scale["notes"][note_index + 4],
            ]

        # minor triad
        if self.modifiers[1]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 2],
                self.scale["notes"][note_index + 4],
            ]

        # seventh
        if self.modifiers[2]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 2],
                self.scale["notes"][note_index + 4],
                self.scale["notes"][note_index + 6],
            ]

        # ninth
        if self.modifiers[3]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 2],
                self.scale["notes"][note_index + 4],
                self.scale["notes"][note_index + 6],
                self.scale["notes"][note_index + 8],
            ]

        # sus2
        if self.modifiers[4]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 1],
                self.scale["notes"][note_index + 4],
            ]

        # sus4
        if self.modifiers[4]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 3],
                self.scale["notes"][note_index + 4],
            ]

        # augmented
        if self.modifiers[5]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 2],
                self.scale["notes"][note_index + 4] + 1,
            ]

        # diminished
        if self.modifiers[6]:
            resolved = [
                self.scale["notes"][note_index],
                self.scale["notes"][note_index + 2],
                self.scale["notes"][note_index + 4] - 1,
            ]

        return resolved

    def on_scale_message(self, message):
        scale_name = {
            20: "major",
            21: "minor",
            22: "natural minor",
            23: "melodic minor",
            24: "dorian",
            25: "locrian",
            26: "lydian",
            27: "mixolydian",
        }.get(message.control)

        self.scale["notes"] = []
        self.scale["size"] = len(Scale._SCALE_PATTERNS[scale_name])

        for octave in range(-1, 9):
            scale = Scale.build_scale(Note.from_note_string(f"C{octave}"), scale_name)
            for idx in range(self.scale["size"]):
                self.scale["notes"].append(scale[idx].midi_note_number())

        print(self.scale["notes"])

    def on_chord_modifier_message(self, message):
        modifier = message.note - 92
        if message.type == "note_on":
            self.modifiers[modifier] = True
            self._in_device.highlight_pad(message.note, Push2Colors.BLUE)

        if message.type == "note_off":
            self.modifiers[modifier] = False
            self._in_device.highlight_pad(message.note, Push2Colors.BLACK)

        print("modifier", self.modifiers)

    def on_note_message(self, message):

        row = (message.note - 36) // 8
        col = (message.note - 36) % 8
        note_index = self.scale["size"] * row + col

        if message.type == "note_on":
            notes = self.modify(note_index)
            self._in_device.highlight_pad(message.note, Push2Colors.GREEN)
            self.propagate(message, notes)

        if message.type == "note_off":
            notes = self.modify(note_index)
            self._in_device.highlight_pad(
                message.note, self.get_pad_default_color(message.note)
            )
            self.propagate(message, notes)

    def on_message(self, message):
        # control message
        if message.type == "control_change" and message.value == 127:
            if 20 <= message.control <= 27:
                self.on_scale_message(message)

        if message.type in ["note_on", "note_off"]:
            if 92 <= message.note <= 99:
                self.on_chord_modifier_message(message)

            if 36 <= message.note <= 91:
                self.on_note_message(message)

    def propagate(self, message, notes):
        logger.info(message)
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
