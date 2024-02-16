import logging
import os
import json
from pathlib import Path

import construct as C
from music_essentials import Note, Scale

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Constants defining MP218 features

_PADS = 16
_PBANKS = 3
_PTOTAL = _PADS * _PBANKS

_DIALS = 6
_DBANKS = 3
_DTOTAL = _DIALS * _DBANKS

# --------------------------------------------------
# Define file format using Construct (v2.9)
# https://github.com/construct/construct

Header = C.Struct(
    C.Const(b"\xf0"),  # SysEx Begin
    C.Const(b"\x47\x00"),  # Mfg ID = Akai
    C.Const(b"\x34"),  # Dev ID = MPD218
    C.Const(b"\x10"),  # CMD = Dump/Load Preset
    C.Const(b"\x04\x1d"),  # Len = 541bytes (7bit stuffed)
    "preset" / C.Byte,
    "name" / C.PaddedString(8, "ascii"),  # Pad with spaces!
    "tempo"
    / C.ExprAdapter(
        C.Int16ub,  # 7bit stuffed - each byte max 0x7F
        ((C.obj_ & 0x7F) + ((C.obj_ & 0x7F00) >> 1)),
        ((C.obj_ & 0x7F) + ((C.obj_ & 0x3F80) << 1)),
    ),
    "division"
    / C.Enum(
        C.Byte,
        DIV_1_4=0,
        DIV_1_4T=1,
        DIV_1_8=2,
        DIV_1_8T=3,
        DIV_1_16=4,
        DIV_1_16T=5,
        DIV_1_32=6,
        DIV_1_32T=7,
    ),
    "swing"
    / C.Enum(
        C.Byte,  # This could be byte value
        SWING_OFF=50,
        SWING_54=54,
        SWING_56=56,
        SWING_58=58,
        SWING_60=60,
        SWING_62=62,
    ),
)

Pad = C.Struct(
    "type"
    / C.Enum(
        C.Byte,
        NOTE=0,
        PROG=1,
        BANK=2,
    ),
    "channel" / C.Byte,
    "note" / C.Byte,  # NOTE only
    "trigger"
    / C.Enum(
        C.Byte,  # NOTE only
        MOMENTARY=0,
        TOGGLE=1,
    ),
    "aftertouch"
    / C.Enum(
        C.Byte,  # NOTE only
        OFF=0,
        CHANNEL=1,
        POLY=2,
    ),
    "program" / C.Byte,  # PROG only
    "msb" / C.Byte,  # BANK only
    "lsb" / C.Byte,  # BANK only
)

Dial = C.Struct(
    "type"
    / C.Enum(
        C.Byte,
        CC=0,
        AFTERTOUCH=1,
        INC_DEC_1=2,
        INC_DEC_2=3,
    ),
    "channel" / C.Byte,
    "midicc" / C.Byte,  # CC and ID2 only
    "min" / C.Byte,  # CC and AT only
    "max" / C.Byte,  # CC and AT only
    "msb" / C.Byte,  # ID1 only
    "lsb" / C.Byte,  # ID1 only
    "value" / C.Byte,  # ID1 only
)

Footer = C.Struct(
    C.Const(b"\xf7"),  # SysEx End
)

Mpd218 = C.Sequence(
    Header,
    C.Array(
        _PBANKS,
        C.Array(
            _PADS,
            Pad,
        ),
    ),
    C.Array(
        _DBANKS,
        C.Array(
            _DIALS,
            Dial,
        ),
    ),
    Footer,
)

# --------------------------------------------------


class MPDApplication:
    """Application entry point."""

    @staticmethod
    def adjust_pad(pad):
        """Convert pad attributes to numeric values"""
        return {
            **pad,
            "trigger": {"momentary": 0, "toggle": 1}.get(pad["trigger"]),
            "type": {"note": 0, "prog": 1, "bank": 2}.get(pad["type"]),
            "aftertouch": {
                "off": 0,
                "channel": 1,
                "poly": 2,
            }.get(pad["aftertouch"]),
        }

    @staticmethod
    def adjust_dial(dial):
        """Convert dial attributes to numeric values"""
        return {
            **dial,
            "type": {"cc": 0, "aftertouch": 1, "incdec1": 2, "incdec2": 3}.get(
                dial["type"]
            ),
        }

    async def run(self, options=None):

        current_dir = os.path.dirname(os.path.realpath(__file__))
        config_file = f"{current_dir}/mpd/" + options.config
        with open(config_file) as f:
            conf = json.loads(f.read())

        pad_template = conf["template"]["pad"]
        dial_template = conf["template"]["dial"]

        header = {
            "preset": 1,
            "name": (conf["name"] + " " * 8)[:8],
            "tempo": conf["tempo"],
            "division": 0,
            "swing": 50,
        }

        if "banks" not in conf:
            conf["banks"] = {
                "a": {"pads": {}, "dials": {}},
                "b": {"pads": {}, "dials": {}},
                "c": {"pads": {}, "dials": {}},
            }

        for scale_conf in conf.get("scales", []):
            bank = scale_conf["bank"]
            if bank not in conf["banks"]:
                conf["banks"][bank] = {"pads": {}}

            scale = Scale.build_scale(
                Note.from_note_string(scale_conf["root"]), scale_conf["type"]
            )

            pad_index = scale_conf["pad"]
            for note in scale:
                conf["banks"][bank]["pads"][str(pad_index)] = {
                    "note": note.midi_note_number()
                }
                pad_index += 1

        pad_banks = [
            [
                self.adjust_pad(
                    {
                        **pad_template,
                        **conf.get("banks", {})
                        .get(bank_name)
                        .get("pads", {})
                        .get(str(pad_index + 1), {}),
                    }
                )
                for pad_index in range(16)
            ]
            for bank_index, bank_name in enumerate(["a", "b", "c"])
        ]

        dial_banks = [
            [
                self.adjust_dial(
                    {
                        **dial_template,
                        **conf.get("banks", {})
                        .get(bank_name)
                        .get("dials", {})
                        .get(str(dial_index + 1), {}),
                    }
                )
                for dial_index in range(6)
            ]
            for bank_index, bank_name in enumerate(["a", "b", "c"])
        ]

        mpd = Mpd218.build(
            [
                header,
                pad_banks,
                dial_banks,
                None,
            ]
        )

        # print(Mpd218.parse(mpd))
        # print(json.dumps(pad_banks, indent=4))
        # print(json.dumps(dial_banks, indent=4))
        # print(mpd)

        basename = Path(config_file).stem
        mpd_file = f"{current_dir}/mpd/{basename}.mpd218"
        with open(mpd_file, "wb+") as f:
            f.write(mpd)
