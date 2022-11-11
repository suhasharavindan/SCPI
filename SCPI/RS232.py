"""
@author: Suhash Aravindan 10/18/2022
@description: RS232 SCPI communication object, instruments and helper functions.
"""
import time
import serial
import serial.tools.list_ports

def read_ports():
    """Find ports to serial connections by assuming USB connection.

    Returns:
        list str: Instrument ports.
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

def read_instruments(filename, conf, instruments, sleep_time=0, meas_time=10000, val_range='DEF', val_res='MIN', channels=None):
    """Take specified measurement from multiple DMMs at every period for a set amount of time.

    Args:
        filename (str): Output file name.
        conf (str, list): Measurement mode. Look at set_CONF function for options.
        instruments (list): Instrument objects.
        sleep_time (float, optional): Sleep time between measurements in sec. Defaults to 0.
        meas_time (int, optional): Total measurement time in sec. Defaults to 10000.
        val_range (int, str or list, optional): Approximate measurement range in standard units. Defaults to "DEF".
        val_res (float or str, optional): Measurement resolution in standard units. Defaults to "MIN".
        channels (list int, optional): Instrument channels to address. Only applicable to MX. Defaults to None.

    Returns:
        np.array: Array of collected measurements
    """
    # Set instruments to list if only one is provided
    if not isinstance(instruments, list):
        instruments = list(instruments)

    # Set measurement mode on instruments
    # If a different conf is needed per instrument, a list should be passed in the same order of the DMMs
    if not isinstance(conf, list):
        conf = [conf] * len(instruments)
    for idx, ins in enumerate(instruments):
        ins.set_CONF(conf[idx], val_range, val_res, channels)
        time.sleep(5)

    time.sleep(10)

    # Start time
    tic = time.time()
    toc = tic

    # Read DMMs
    try:
        while (toc - tic) < meas_time:
            toc = time.time()
            measurements = []
            for ins in instruments:
                val = ins.read_meas()
                if isinstance(val, list):
                    measurements.extend(val)
                else:
                    measurements.append(val)

            vals = [(toc-tic)] + measurements
            print(*vals, sep='\t')

            # Stream values into file as measurement goes on
            if filename: # Skip write to file if no filename provided
                with open(filename, 'a') as f:
                    f.write(','.join([str(val) for val in vals]) + '\n')

            # A pause between reads
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        # End measurements
        pass

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

        time.sleep(5)
        if self.ser.is_open:
            self.ser.write("SYST:REM\n".encode())

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
            float or string: Measurement.
        """
        try:
            self.ser.write("READ?\n".encode())
            time.sleep(5)
            temp = self.ser.readline()
            output = float(temp.decode()[:-2])
        except ValueError:
            output = temp.decode()[:-2]

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

    def set_CONF(self, conf, val_range='DEF', val_res='MIN', _=None):
        """Set DMM to measurement mode.

        Args:
            conf (str): Measurement mode.
            val_range (int, str or list): Approximate range of measurement in standard units. Defaults to "DEF".
            val_res (float or str): Measurement resolution in standard units. Defaults to "MIN".
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

    def set_CONF(self, conf, channels, val_range='DEF', val_res='MIN'):
        """Set MX to measurement mode.

        Args:
            conf (str): Measurement mode.
            channels (list int): Channel indices.
            val_range (int, str or list): Approximate range of measurement in standard units. Defaults to "DEF".
            val_res (float or str): Measurement resolution in standard units. Defaults to "MIN".
        """

        if isinstance(val_range, list):
            for idx, ch in enumerate(channels):
                params = f"{val_range[idx]}, {val_res}, (@{ch})"
                super().set_CONFIG(conf, params)
        else:
            channel_str = ",".join(str(ch) for ch in channels)
            params = f"{val_range}, {val_res}, (@{channel_str})"
            super().set_CONFIG(conf, params)

    def read_meas(self):
        """Read measurement.

        Returns:
            list float: Parsed measurement read response.
        """
        ret = super().read_meas()
        if isinstance(ret, str):
            res = [float(val) for val in ret.split(',')]
        else:
            res = ret
        return res
