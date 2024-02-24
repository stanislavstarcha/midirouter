import logging

import cairo
from music_essentials import Note, Scale

from midirouter.device.push2 import Push2Colors
from midirouter.routers.push2.pages import Push2Page

logger = logging.getLogger(__name__)


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

    _octave = 1
    _modifiers = [False] * 16
    _prev_modifiers = [False] * 16

    # when true modifiers work in a toggle mode
    _latch_mode = False

    # current scale index
    _scale_index: int = None
    # current scale name
    _scale_name: str = None
    # current scale size
    _scale_size: int = 7
    # current scale notes
    _scale_notes: list = None
    # current scale root note
    _scale_root_note: str = "C"
    # current scale key notes
    _scale_key_notes: list = []

    # current chord state
    _chord_notes = ""
    _chord_type = ""
    _chord_modifier_a = ""
    _chord_modifier_b = ""

    # current notes pressed
    _notes_pressed = set()
    _notes_playing = set()

    _modifier_name: str = ""

    def initialize(self):
        self._device.add_callback(self.on_message)
        self.initialize_controls()
        self.initialize_scales()
        self.initialize_pads()
        self.initialize_modifiers()
        self.set_scale(20)

    def initialize_controls(self):
        self._device.highlight_control(54)
        self._device.highlight_control(55)

    def initialize_scales(self):
        for cc, name in self.SCALES.items():
            self._device.highlight_control(cc)

    def initialize_pads(self):
        for i in range(36, 84):
            self._device.highlight_pad(i, self.get_pad_default_color(i))

    def initialize_modifiers(self):
        for pad, name in self.MODIFIERS.items():
            self._device.highlight_pad(pad, self.MODIFIER_COLORS[name])

    def build_chord(self, note_index, modifiers):
        self._chord_type = ""
        self._chord_modifier_a = ""
        self._chord_modifier_b = ""

        names = set(
            [self.MODIFIERS[idx + 84] for idx, state in enumerate(modifiers) if state]
        )

        if not names:
            return [self._scale_notes[note_index]]

        # major chord
        names.add("triad")
        self._chord_type = "maj"
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

        scale = Scale.build_scale(
            Note.from_note_string(f"{self._scale_root_note}0"),
            self._scale_name,
        )

        self._scale_key_notes = [str(note) for note in scale][: self._scale_size]

        for octave in range(-1, 9):
            scale = Scale.build_scale(
                Note.from_note_string(f"{self._scale_root_note}{octave}"),
                self._scale_name,
            )
            for idx in range(self._scale_size):
                self._scale_notes.append(scale[idx].midi_note_number())

    def on_scale_message(self, message):
        self._scale_index = message.control
        self.set_scale(self._scale_index)

    def on_octave_message(self, message):

        if message.control == 54 and self._octave > -1:
            self._octave -= 1

        if message.control == 55 and self._octave < 2:
            self._octave += 1

    def on_chord_modifier_message(self, message):
        self._chord_type = ""
        self._chord_modifier_a = ""
        self._chord_modifier_b = ""

        index = message.note - 84

        pad_color = self.MODIFIER_COLORS[self.MODIFIERS[message.note]]

        if self._latch_mode:
            if message.type == "note_on":
                self._modifiers[index] = not self._modifiers[index]
            if self._modifiers[index]:
                pad_color = Push2Colors.BLUE

        else:
            if message.type == "note_on":
                self._modifiers[index] = True
                pad_color = Push2Colors.BLUE

            if message.type == "note_off":
                self._modifiers[index] = False

        to_play = set()
        to_stop = set()

        for note_index in self._notes_pressed:
            last_chord = self.build_chord(note_index, self._prev_modifiers)
            to_stop.update(set(last_chord) - {self._scale_notes[note_index]})

            chord = self.build_chord(note_index, self._modifiers)
            to_play.update(set(chord) - {self._scale_notes[note_index]})

        to_stop -= to_play
        to_play -= self._notes_playing

        if to_stop:
            self._notes_playing -= to_stop
            self._on_midi_out(
                msg_type="note_off",
                velocity=message.velocity,
                notes=to_stop,
                channel=message.channel,
            )

        if to_play:
            self._notes_playing.update(to_play)
            self._on_midi_out(
                msg_type="note_on",
                velocity=message.velocity,
                notes=to_play,
                channel=message.channel,
            )

        self._prev_modifiers = list(self._modifiers)
        self._device.highlight_pad(message.note, pad_color)

    def on_note_message(self, message):

        base = 36
        octave_diff = self._octave - (-1)
        pad_note = message.note + octave_diff * 8

        row = (pad_note - base) // 8
        col = (pad_note - base) % 8
        note_index = self._scale_size * row + col
        chord = self.build_chord(note_index, self._modifiers)

        pad_color = Push2Colors.GREEN
        if message.type == "note_on":
            self._notes_pressed.add(note_index)
            self._notes_playing.update(set(chord))

        if message.type == "note_off":
            pad_color = self.get_pad_default_color(pad_note)
            self._notes_pressed.remove(note_index)
            self._notes_playing -= set(chord)

        self._device.highlight_pad(message.note, pad_color)
        self._on_midi_out(
            msg_type=message.type,
            velocity=message.velocity,
            notes=chord,
            channel=message.channel,
        )

    def on_latch_mode_message(self, message):
        self._latch_mode = not self._latch_mode
        control_color = Push2Colors.WHITE if self._latch_mode else Push2Colors.BLACK
        self._device.highlight_control(48, control_color)

    def on_message(self, message):
        try:
            # control message
            if message.type == "control_change" and message.value == 127:

                if message.control == 48:
                    self.on_latch_mode_message(message)

                if 20 <= message.control <= 27:
                    self.on_scale_message(message)

                if 54 <= message.control <= 55:
                    self.on_octave_message(message)

            if message.type in ["note_on", "note_off"]:
                if 84 <= message.note <= 99:
                    self.on_chord_modifier_message(message)

                if 36 <= message.note <= 83:
                    self.on_note_message(message)
        except Exception as e:
            logger.exception(e)

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

        ctx.move_to(10, 30)
        ctx.set_font_size(20)
        ctx.show_text(
            self._chord_modifier_a + self._chord_modifier_b + self._chord_type
        )

        for idx, midi_note in enumerate(sorted(self._notes_playing)):
            ctx.set_font_size(40)
            ctx.move_to(10 + idx * 100, 100)
            note = Note.from_midi_num(midi_note)
            accidental = note.accidental if note.accidental else ""
            note_str = note.pitch + accidental
            ctx.show_text(note_str)

            ctx.set_font_size(10)
            ctx.move_to(15 + 25 * len(note_str) + idx * 100, 80)
            ctx.show_text(str(note.octave))

        # if self._notes_pressed:
        #     for idx, note_index in enumerate(self._notes_pressed.copy()):
        #         note = str(Note.from_midi_num(self._scale_notes[note_index]))
        #         ctx.move_to(10 + idx * 200, font_size * 2)

        ctx.set_font_size(14)
        for scale_index, scale_name in self.SCALES.items():
            if scale_index == self._scale_index:
                ctx.set_source_rgb(1, 1, 1)
            else:
                ctx.set_source_rgb(0.4, 0.4, 0.4)

            ctx.move_to(10 + 122 * (scale_index - 20), 150)
            ctx.show_text(scale_name)

        return self.prepare(surface.get_data())
