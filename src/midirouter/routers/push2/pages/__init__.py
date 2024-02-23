import cairo
import numpy

HEIGHT = 160
WIDTH = 960
DISPLAY_LINE_FILLER_BYTES = 128
NP_DISPLAY_FRAME_XOR_PATTERN = numpy.array(
    [0xE7F3, 0xE7FF] * (((WIDTH + (DISPLAY_LINE_FILLER_BYTES // 2)) * HEIGHT) // 2),
    dtype=numpy.uint16,
)


class Push2Page:

    WIDTH = WIDTH
    HEIGHT = HEIGHT

    _device = None

    # callback to send midi notes outes
    _on_midi_out = None

    def __init__(self, device, on_midi_out):
        self._device = device
        self._on_midi_out = on_midi_out

    def get_surface(self):
        return cairo.ImageSurface(cairo.FORMAT_RGB16_565, WIDTH, HEIGHT)

    @staticmethod
    def rgb565_to_bgr565(rgb565_frame):
        r_filter = int("1111100000000000", 2)
        g_filter = int("0000011111100000", 2)
        b_filter = int("0000000000011111", 2)
        frame_r_filtered = numpy.bitwise_and(rgb565_frame, r_filter)
        frame_r_shifted = numpy.right_shift(
            frame_r_filtered, 11
        )  # Shift bits so R compoenent goes to the right
        frame_g_filtered = numpy.bitwise_and(rgb565_frame, g_filter)
        frame_g_shifted = (
            frame_g_filtered  # No need to shift green, it stays in the same position
        )
        frame_b_filtered = numpy.bitwise_and(rgb565_frame, b_filter)
        frame_b_shifted = numpy.left_shift(
            frame_b_filtered, 11
        )  # Shift bits so B compoenent goes to the left
        return (
            frame_r_shifted + frame_g_shifted + frame_b_shifted
        )  # Combine all channels

    def prepare(self, buffer):

        frame = numpy.ndarray(
            shape=(self.HEIGHT, self.WIDTH), dtype=numpy.uint16, buffer=buffer
        )
        frame = frame.transpose()

        width = WIDTH + DISPLAY_LINE_FILLER_BYTES // 2
        height = HEIGHT
        prepared_frame = numpy.zeros(shape=(width, height), dtype=numpy.uint16)
        prepared_frame[0 : frame.shape[0], 0 : frame.shape[1]] = frame
        prepared_frame = prepared_frame.transpose().flatten()
        prepared_frame = self.rgb565_to_bgr565(prepared_frame)
        prepared_frame = prepared_frame.byteswap()  # Change to little endian
        prepared_frame = numpy.bitwise_xor(prepared_frame, NP_DISPLAY_FRAME_XOR_PATTERN)

        return prepared_frame.byteswap().tobytes()
