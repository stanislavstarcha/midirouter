import asyncio
import logging

import usb.core

ABLETON_VENDOR_ID = 0x2982
PUSH2_PRODUCT_ID = 0x1967
USB_TRANSFER_TIMEOUT = 1000

DISPLAY_FRAME_HEADER = [
    0xFF,
    0xCC,
    0xAA,
    0x88,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
    0x00,
]

logger = logging.getLogger(__name__)


class Push2Display:

    _usb_endpoint = None
    _connected = False
    _on_connected = None
    _on_disconnected = None

    def __init__(self, on_connected, on_disconnected):
        self._on_connected = on_connected
        self._on_disconnected = on_disconnected

    async def connect(self):
        usb_device = usb.core.find(
            idVendor=ABLETON_VENDOR_ID, idProduct=PUSH2_PRODUCT_ID
        )
        device_configuration = usb_device.get_active_configuration()
        if device_configuration is None:
            usb_device.set_configuration()

        interface = device_configuration[(0, 0)]

        while True:
            descriptor = usb.util.find_descriptor(
                interface,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                == usb.util.ENDPOINT_OUT,
            )
            if descriptor:
                break
            logger.warning("Push2 display not found. Waiting...")
            await asyncio.sleep(5)

        self._usb_endpoint = descriptor
        if self._on_connected:
            self._on_connected()

    def show(self, frame):
        try:
            self._usb_endpoint.write(DISPLAY_FRAME_HEADER, USB_TRANSFER_TIMEOUT)
            self._usb_endpoint.write(frame, USB_TRANSFER_TIMEOUT)
        except usb.core.USBError:
            if self._on_disconnected:
                self._on_disconnected()
