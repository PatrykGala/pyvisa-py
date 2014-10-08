# -*- coding: utf-8 -*-
"""
    pyvisa-py.usb
    ~~~~~~~~~~~~~

    Serial Session implementation using PyUSB.


    :copyright: 2014 by PyVISA-py Authors, see AUTHORS for more details.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import division, unicode_literals, print_function, absolute_import

from pyvisa import constants

from .sessions import Session

try:
    import usb
    from .protocols import usbtmc, usbutil
except ImportError as e:
    Session.register_unavailable(constants.InterfaceType.usb, 'INSTR',
                                 'Please install PyUSB to use this resource type.\n%s' % e)
    raise


StatusCode = constants.StatusCode
SUCCESS = StatusCode.success


@Session.register(constants.InterfaceType.usb, 'INSTR')
class USBSession(Session):
    """Base class for drivers that communicate with instruments
    via usb port using pyUSB
    """

    #: Configuration number to be used. If None, the default will be used.
    CONFIGURATION = None
    #: Interface index it be used
    INTERFACE = (0, 0)
    #: Receive and Send endpoints to be used. If None the first IN (or OUT) BULK
    #: endpoint will be used.
    ENDPOINTS = (None, None)

    TIMEOUT = 1000

    @staticmethod
    def list_resources():
        out = []
        fmt = 'USB%(board)s::%(manufacturer_id)s::%(model_code)s::' \
              '%(serial_number)s::%(usb_interface_number)s::INSTR'
        for dev in usbtmc.find_tmc_devices():
            nfo = usbutil.DeviceInfo.from_device(dev)
            intfc = usbutil.find_interfaces(dev, bInterfaceClass=0xfe, bInterfaceSubClass=3)
            try:
                intfc = intfc[0].index
            except (IndexError, AttributeError):
                intfc = 0
            out.append(fmt % dict(board=0,
                                  manufacturer_id=dev.idVendor,
                                  model_code=dev.idProduct,
                                  serial_number=nfo.serial_number,
                                  usb_interface_number=intfc))
        return out


    def after_parsing(self):
        self.interface = usbtmc.USBTMC(int(self.parsed['manufacturer_id']),
                                       int(self.parsed['model_code']),
                                       self.parsed['serial_number'])

    def read(self, count):
        """Reads data from device or interface synchronously.

        Corresponds to viRead function of the VISA library.

        :param count: Number of bytes to be read.
        :return: data read, return value of the library call.
        :rtype: bytes, VISAStatus
        """
        ret = b''
        term_char, _ = self.get_attribute(constants.VI_ATTR_TERMCHAR)
        while True:
            ret += self.interface.read(1)
            if ret[-1:] == term_char:
                # TODO: What is the correct success code??
                return ret, StatusCode.termination_char
            #TODO: Should we stop here as well?
            if len(ret) == count:
                return ret, StatusCode.success_max_count_read
            else:
                return ret, StatusCode.error_timeout

        return ret, SUCCESS

    def write(self, data):
        """Writes data to device or interface synchronously.

        Corresponds to viWrite function of the VISA library.

        :param data: data to be written.
        :type data: bytes
        :return: Number of bytes actually transferred, return value of the library call.
        :rtype: int, VISAStatus
        """

        send_end, _ = self.get_attribute(constants.VI_ATTR_SEND_END_EN)

        count = self.interface.write(data)

        return count, SUCCESS

    def close(self):
        self.interface.close()

    def _get_attribute(self, attribute):
        pass

    def _set_attribute(self, attribute, attribute_state):
        pass

    @property
    def timeout(self):
        pass

    @timeout.setter
    def timeout(self, value):
        pass

