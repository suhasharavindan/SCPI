"""
@author: Suhash Aravindan 10/18/2022
@description: RS232 SCPI communication object, instruments and helper functions.
"""
import time
import numpy as np
import serial
import serial.tools.list_ports

def read_ports():
    """Find ports to serial connections by assuming USB connection.

    Returns:
        list str: Instrunent ports.
    """
    ports = []
    for comport in serial.tools.list_ports.comports():
        if 'USB' in comport.description:
            ports.append(comport.device)

    return ports

def init_instruments(instrument_type):
    """Create objects for all connected instruments.

    Args:
        instrument_type (single or list of objects): Instrument object. If list of different objects, should be provided in the order of the ports.

    Returns:
        list: Instrument objects.
    """
    instruments = []
    ports = read_ports()

    if isinstance(instrument_type, list):
        for cnt, port in enumerate(ports):
            ins = instrument_type[cnt](port)
            instruments.append(ins)
    else:
        for port in ports:
            ins = instrument_type(port)
            instruments.append(ins)

    return instruments

def read_instruments(conf, instruments, sleep_time=0, meas_time=10000, val_range=1, val_res=1e-6, channels=None):
    """Take specified measurement from multiple DMMs at every period for a set amount of time.

    Args:
        conf (str): Measurement mode. Look at set_CONF function for options.
        instruments (list): Instrument objects.
        sleepTime (float, optional): Sleep time between measurements in sec. Defaults to 0.
        meas_time (int, optional): Total measurement time in sec. Defaults to 10000.
        val_range (int or list, optional): Approximate measurement range in standard units. Defaults to 1.
        val_res (float, optional): Measurement resolution in standard units. Defaults to 1e-6.
        channels (list int, optional): Instrument channels to address. Only applicable to MX. Defaults to None.

    Returns:
        np.array: Array of collected measurements
    """
    # Set instruments to list if only one is provided
    if not isinstance(instruments, list):
        instruments = list(instruments)

    # Set measurement mode on instruments
    # If a different range is needed per instrument, a list should be passed in the same order of the DMMs
    if isinstance(val_range, list):
        for idx, ins in enumerate(instruments):
            ins.set_CONF(conf, val_range[idx], val_res, channels)
    else:
        for ins in instruments:
            ins.set_CONF(conf, val_range, val_res, channels)

    time.sleep(2)
    output = []

    # Start time
    tic = time.time()
    toc = tic

    # Read DMMs
    try:
        while (toc - tic) < meas_time:
            toc = time.time()
            measurements = []
            for ins in instruments:
                measurements.append(ins.read_meas())

            vals = [(toc-tic)] + measurements
            print(*vals, sep='\t')
            output.append(vals)

            # A pause is required between reads
            time.sleep(sleep_time)

        return np.array(output)

    except KeyboardInterrupt:
        # End measurements
        return np.array(output)

class RS232:
    """RS232 serial SCPI communication object."""

    def __init__(self, port_num, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, bytesize=serial.EIGHTBITS, xonxoff=True):
        """Initialize serial connection.

        Args:
            port_num (str): Serial port.
            baudrate (int, optional): Serial baud rate. Defaults to 9600.
            parity (str, optional): Serial parity. Defaults to serial.PARITY_NONE.
            stopbits (int, optional): Serial stop bits. Defaults to serial.STOPBITS_TWO.
            bytesize (int, optional): Serial byte size. Defaults to serial.EIGHTBITS.
            xonxoff (bool, optional): Software flow control. Defaults to True.
        """
        self.ser = serial.Serial(port = port_num,
                                 baudrate = baudrate,
                                 parity = parity,
                                 stopbits = stopbits,
                                 bytesize = bytesize,
                                 xonxoff = xonxoff)

        time.sleep(0.5)
        if self.ser.is_open:
            self.ser.write("SYSTem:REMote\n".encode())


    def __del__(self):
        """Close serial port upon object delection."""
        self.ser.close()

    def read_ID(self):
        """Read serial ID.

        Returns:
            str: Serial ID.
        """
        output = self.ser.write("*IDN?\n".encode())
        return output

    def set_CONFIG(self, conf, params):
        """Set instrument to measurement mode.

        Args:
            conf (str): Measurement mode.
            params (str): Configuration parameters.
        """
        if conf == "DCV": # DC voltage
            self.ser.write(f"CONF:VOLT:DC {params}\n".encode())
        elif conf == "ACV": # AC voltage
            self.ser.write(f"CONF:VOLT:AC {params}\n".encode())
        elif conf == "DCI": # DC current
            self.ser.write(f"CONF:CURR:DC {params}\n".encode())
        elif conf == "ACI": # AC current
            self.ser.write(f"CONF:CURR:AC {params}\n".encode())
        elif conf == "RES2": # 2-wire resistance
            self.ser.write(f"CONF:RES {params}\n".encode())
        elif conf == "RES4": # 4-wire resistance
            self.ser.write(f"CONF:FRES {params}\n".encode())
        elif conf == "FREQ": # Frequency
            self.ser.write(f"CONF:FREQ {params}\n".encode())
        elif conf == "PER": # Period
            self.ser.write(f"CONF:PER {params}\n".encode())
        else:
            pass

    def set_TRIG(self, val="IMM"):
        """Set trigger for measurement.

        Args:
            val (str, optional): Trigger source. Can be IMMediate, BUS, or EXTernal. Defaults to "IMM".
        """
        self.ser.write(f"TRIG:SOUR {val}\n".encode())

    def read_meas(self):
        """Take a measurement.

        Returns:
            float: Measurement.
        """
        try:
            self.ser.write("READ?\n".encode())
            temp = self.ser.readline()
            output = float(temp[:-2])
        except ValueError:
            print(temp)
            temp = self.ser.readline()
            output = float(temp[:-2])

        return output

class DMM34401A(RS232):
    """DMM 34401A object."""

    def __init__(self, port_num, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, bytesize=serial.EIGHTBITS, xonxoff=True):
        """Initialize serial connection for DMM object.

        Args:
            port_num (str): Serial port.
            baudrate (int, optional): Serial baud rate. Defaults to 9600.
            parity (str, optional): Serial parity. Defaults to serial.PARITY_NONE.
            stopbits (int, optional): Serial stop bits. Defaults to serial.STOPBITS_TWO.
            bytesize (int, optional): Serial byte size. Defaults to serial.EIGHTBITS.
            xonxoff (bool, optional): Software flow control. Defaults to True.
        """
        super().__init__(port_num, baudrate, parity, stopbits, bytesize, xonxoff)

    def set_CONF(self, conf, val_range, val_res, _=None):
        """Set DMM to measurement mode.

        Args:
            conf (str): Measurement mode.
            val_range (int): Approximate range of measurement in standard units.
            val_res (float): Measurement resolution in standard units.
            _ : Placeholder to match arguments for MX objects.
        """
        params = f"{val_range}, {val_res}"
        super().set_CONFIG(conf, params)

class MX34970A(RS232):
    """MX 34970A object."""

    def __init__(self, port_num, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, bytesize=serial.EIGHTBITS, xonxoff=True):
        """Initialize serial connection for MX object.

        Args:
            port_num (str): Serial port.
            baudrate (int, optional): Serial baud rate. Defaults to 9600.
            parity (str, optional): Serial parity. Defaults to serial.PARITY_NONE.
            stopbits (int, optional): Serial stop bits. Defaults to serial.STOPBITS_TWO.
            bytesize (int, optional): Serial byte size. Defaults to serial.EIGHTBITS.
            xonxoff (bool, optional): Software flow control. Defaults to True.
        """
        super().__init__(port_num, baudrate, parity, stopbits, bytesize, xonxoff)

    def set_CONF(self, conf, val_range, val_res, channels):
        """Set MX to measurement mode.

        Args:
            conf (str): Measurement mode.
            channels (list int): Channel indices.
            val_range (int): Approximate range of measurement in standard units.
            val_res (float): Measurement resolution in standard units.
        """

        channel_str = ",".join(str(ch) for ch in channels)
        params = f"{val_range}, {val_res}, (@{channel_str})"
        super().set_CONFIG(conf, params)
