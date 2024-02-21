import mido


def get_in_ports():
    return mido.get_input_names()


def get_out_ports():
    return mido.get_output_names()
