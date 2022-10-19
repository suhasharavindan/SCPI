"""
Example use of package.
"""

from SCPI.RS232 import init_instruments, read_instruments, DMM34401A

instruments = init_instruments(DMM34401A)
read_instruments('RES2', instruments, sleep_time=3, meas_time=30, val_range=100, val_res=1e-6)
