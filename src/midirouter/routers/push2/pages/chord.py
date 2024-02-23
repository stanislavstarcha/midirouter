import cairo
from music_essentials import Note, Scale

from midirouter.device.push2 import Push2Colors
from midirouter.routers.push2.pages import Push2Page


class Push2ChordPage(Push2Page):

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

    MODIFIERS = {
        84: "min",
        85: "sus4",
        86: "dim",
        87: "min",
        88: "sus4",
        89: "dim",
        90: "min",
        91: "sus4",
        92: "triad",
        93: "sus2",
        94: "aug",
        95: "maj7",
        96: "sus2",
        97: "aug",
        98: "inv",
        99: "sus2",
    }

    MODIFIER_COLORS = {
        "min": 30,
        "sus2": 36,
        "sus4": 36,
        "dim": 40,
        "aug": 40,
        "triad": 1,
        "maj7": 1,
        "inv": 1,
    }

    modifiers = [False] * 16

    # current scale index
    _scale_index: int = None
    # current scale name
    _scale_name: str = None
    # current scale size
    _scale_size: int = 7
    # current scale notes
    _scale_notes: list = None

    # current chord state
    _chord_notes = ""
    _chord_type = ""
    _chord_modifier_a = ""
    _chord_modifier_b = ""

    # current notes pressed
    _notes_on = set()

    _modifier_name: str = ""

    def initialize(self):
        self._device.add_callback(self.on_message)
        self.initialize_scales()
        self.initialize_pads()
        self.initialize_modifiers()
        self.set_scale(20)

    def initialize_scales(self):
        for cc, name in self.SCALES.items():
            self._device.highlight_control(cc)

    def initialize_pads(self):
        for i in range(36, 84):
            self._device.highlight_pad(i, self.get_pad_default_color(i))

    def initialize_modifiers(self):
        for pad, name in self.MODIFIERS.items():
            self._device.highlight_pad(pad, self.MODIFIER_COLORS[name])

    def modify(self, note_index):

        self._chord_type = ""
        self._chord_modifier_a = ""
        self._chord_modifier_b = ""

        names = set(
            [
                self.MODIFIERS[idx + 84]
                for idx, state in enumerate(self.modifiers)
                if state
            ]
        )

        if not names:
            return [self._scale_notes[note_index]]

        # major chord
        names.add("triad")
        chord = [
            self._scale_notes[note_index],
            self._scale_notes[note_index + 2],
            self._scale_notes[note_index + 4],
        ]

        # base major seventh chord
        if "maj7" in names:
            self._chord_type = "maj7"
            chord = [
                self._scale_notes[note_index],
                self._scale_notes[note_index + 2],
                self._scale_notes[note_index + 4],
                self._scale_notes[note_index + 6],
            ]

        # ------------------------------------------------------------

        # sus4 precedence over sus2
        if "sus2" in names and "sus4" in names:
            names.remove("sus2")

        # aug precedence over dim
        if "aug" in names and "dim" in names:
            names.remove("dim")

        # sus2/4 precedence over min
        if "min" in names and ("sus2" in names or "sus4" in names):
            names.remove("min")

        # dim/aug precedence over sus2/4
        if ("dim" in names or "aug" in names) and ("sus2" in names or "sus4" in names):
            if "sus2" in names:
                names.remove("sus2")
            if "sus4" in names:
                names.remove("sus4")

        # ------------------------------------------------------------
        if "min" in names:
            self._chord_modifier_a = "min"
        if "dim" in names:
            self._chord_modifier_b = "dim"
        if "aug" in names:
            self._chord_modifier_b = "aug"
        if "sus2" in names:
            self._chord_modifier_b = "sus2"
        if "sus4" in names:
            self._chord_modifier_b = "sus4"

        if "min" in names and "triad" in names:
            chord[1] -= 1

        if "min" in names and "maj7" in names:
            chord[1] -= 1
            chord[3] -= 1

        if "sus2" in names:
            chord[1] = self._scale_notes[note_index + 1]

        if "sus4" in names:
            chord[1] = self._scale_notes[note_index + 3]

        if "dim" in names and "triad" in names:
            chord[1] -= 1
            chord[2] -= 1

        if "dim" in names and "maj7" in names:
            chord[1] -= 1
            chord[2] -= 1
            chord[3] -= 1

        if "aug" in names and "triad" in names:
            chord[2] += 1

        if "aug" in names and "maj7" in names:
            chord[2] += 1
            chord[3] += 1

        return chord

    def set_scale(self, index):
        self._scale_name = self.SCALES.get(index)

        for scale_cc in self.SCALES.keys():
            self._device.highlight_control(scale_cc, Push2Colors.DARK_GRAY)
        self._device.highlight_control(index, Push2Colors.WHITE)

        self._scale_notes = []
        self._scale_size = len(Scale._SCALE_PATTERNS[self._scale_name])

        for octave in range(-1, 9):
            scale = Scale.build_scale(
                Note.from_note_string(f"C{octave}"), self._scale_name
            )
            for idx in range(self._scale_size):
                self._scale_notes.append(scale[idx].midi_note_number())

    def on_scale_message(self, message):
        self._scale_index = message.control
        self.set_scale(self._scale_index)

    def on_chord_modifier_message(self, message):
        index = message.note - 84
        if message.type == "note_on":
            self.modifiers[index] = True
            self._device.highlight_pad(message.note, Push2Colors.BLUE)

        if message.type == "note_off":
            self.modifiers[index] = False
            self._device.highlight_pad(
                message.note, self.MODIFIER_COLORS[self.MODIFIERS[message.note]]
            )

    def on_note_message(self, message):

        row = (message.note - 36) // 8
        col = (message.note - 36) % 8
        note_index = self._scale_size * row + col

        if message.type == "note_on":
            self._device.highlight_pad(message.note, Push2Colors.GREEN)
            self._notes_on.add(str(Note.from_midi_num(self._scale_notes[note_index])))
            notes = self.modify(note_index)
            self._on_midi_out(message, notes)

        if message.type == "note_off":
            self._device.highlight_pad(
                message.note, self.get_pad_default_color(message.note)
            )
            self._notes_on.remove(
                str(Note.from_midi_num(self._scale_notes[note_index]))
            )
            notes = self.modify(note_index)
            self._on_midi_out(message, notes)

    def on_message(self, message):
        # control message
        if message.type == "control_change" and message.value == 127:
            if 20 <= message.control <= 27:
                self.on_scale_message(message)

        if message.type in ["note_on", "note_off"]:
            if 84 <= message.note <= 99:
                self.on_chord_modifier_message(message)

            if 36 <= message.note <= 83:
                self.on_note_message(message)

    def get_pad_default_color(self, note):
        color = Push2Colors.DARK_GRAY
        if (note - 36) % 8 == 0:
            color = Push2Colors.LIGHT_GRAY
        if (note - 32) % 8 == 0:
            color = Push2Colors.LIGHT_GRAY
        return color

    def build(self):

        # Prepare cairo canvas
        surface = self.get_surface()
        ctx = cairo.Context(surface)

        # Add text with encoder name and value
        ctx.set_source_rgb(1, 1, 1)
        font_size = self.HEIGHT // 3

        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        if self._notes_on:
            for idx, note in enumerate(self._notes_on.copy()):
                ctx.set_font_size(font_size)
                ctx.move_to(10 + idx * 200, font_size * 2)
                ctx.show_text(
                    note
                    + self._chord_modifier_a
                    + self._chord_modifier_b
                    + self._chord_type
                )

        ctx.set_font_size(14)
        for scale_index, scale_name in self.SCALES.items():
            if scale_index == self._scale_index:
                ctx.set_source_rgb(1, 1, 1)
            else:
                ctx.set_source_rgb(0.4, 0.4, 0.4)

            ctx.move_to(10 + 122 * (scale_index - 20), 150)
            ctx.show_text(scale_name)

        return self.prepare(surface.get_data())
