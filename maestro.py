import serial
import time
from sys import version_info
import os

PY2 = version_info[0] == 2  # Running Python 2.x?

trajectory = [
    [1500, 1500, 1500, 1500, 1500],
    [2500, 1500, 1500, 1500, 1500],
    [1000, 1500, 1500, 1500, 1500],
    [1500, 1500, 1500, 1500, 1500],
]


#
# ---------------------------
# Maestro Servo Controller
# ---------------------------
#
# Support for the Pololu Maestro line of servo controllers
#
# Steven Jacobs -- Aug 2013
# https://github.com/FRC4564/Maestro/
#
# These functions provide access to many of the Maestro's capabilities using the
# Pololu serial protocol
#

str_to_byte = {

}

class Controller:
    # When connected via USB, the Maestro creates two virtual serial ports
    # /dev/ttyACM0 for commands and /dev/ttyACM1 for communications.
    # Be sure the Maestro is configured for "USB Dual Port" serial mode.
    # "USB Chained Mode" may work as well, but hasn't been tested.
    #
    # Pololu protocol allows for multiple Maestros to be connected to a single
    # serial port. Each connected device is then indexed by number.
    # This device number defaults to 0x0C (or 12 in decimal), which this module
    # assumes.  If two or more controllers are connected to different serial
    # ports, or you are using a Windows OS, you can provide the tty port.  For
    # example, '/dev/ttyACM2' or for Windows, something like 'COM3'.
    def __init__(self, tty_str='/dev/ttyACM0', device=0x0c):

        self.tty_str = tty_str
        self.tty_port_exists = False
        self.tty_port_connection_established = False
        # Command lead-in and device number are sent for each Pololu serial command.
        self.timeout = 1
        self.last_cmd_send = ''
        self.pololu_cmd = chr(0xaa) + chr(device)
        self.last_exception = ''
        self.last_set_target_vector = []

        # Track target position for each servo. The function isMoving() will
        # use the Target vs Current servo position to determine if movement is
        # occuring.  Upto 24 servos on a Maestro, (0-23). target_positions start at 0.
        self.target_positions = [0] * 24
        # Servo minimum and maximum targets can be restricted to protect components.
        self.Mins = [0] * 24
        self.Maxs = [0] * 24

        self.establish_connection()

    def establish_connection(self):
        try:
            self.usb = serial.Serial(self.tty_str, timeout=1)
            self.tty_port_exists = True
            self.tty_port_connection_established = True
        except Exception as e:
            self.last_exception = e

    # Cleanup by closing USB serial port
    def close(self):
        self.usb.close()

    # Send a Pololu command out the serial port
    def send(self, cmd):
        self.last_cmd_send = cmd
        if self.establish_connection:
            cmd_str = self.pololu_cmd + cmd
            if PY2:
                out = self.usb.write(cmd_str)
            else:
                out = self.usb.write(bytes(cmd_str, 'latin-1'))
        else:
            out = -1
        return out

    def read(self):

        if self.usb.is_open:

            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.usb.in_waiting == 1:
                    return ord(self.usb.read())
        else:
            return -1

    # Set channels min and max value range.  Use this as a safety to protect
    # from accidentally moving outside known safe parameters. A setting of 0
    # allows unrestricted movement.
    #
    # ***Note that the Maestro itself is configured to limit the range of servo travel
    # which has precedence over these values.  Use the Maestro Control Center to configure
    # ranges that are saved to the controller.  Use setRange for software controllable ranges.
    def setRange(self, chan, min, max):
        self.Mins[chan] = min
        self.Maxs[chan] = max

    # Return Minimum channel range value
    def getMin(self, chan):
        return self.Mins[chan]

    # Return Maximum channel range value
    def getMax(self, chan):
        return self.Maxs[chan]

    # Set channel to a specified target value.  Servo will begin moving based
    # on Speed and Acceleration parameters previously set.
    # Target values will be constrained within Min and Max range, if set.
    # For servos, target represents the pulse width in of quarter-microseconds
    # Servo center is at 1500 microseconds, or 6000 quarter-microseconds
    # Typcially valid servo range is 3000 to 9000 quarter-microseconds
    # If channel is configured for digital output, values < 6000 = Low ouput
    def set_target(self, chan: object, target: object) -> object:
        self.target_positions[chan] = target
        target = round(target * 4);
        # if Min is defined and Target is below, force to Min
        if self.Mins[chan] > 0 and target < self.Mins[chan]:
            target = self.Mins[chan]
        # if Max is defined and Target is above, force to Max
        if self.Maxs[chan] > 0 and target > self.Maxs[chan]:
            target = self.Maxs[chan]
        #
        lsb = target & 0x7f  # 7 bits for least significant byte
        msb = (target >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = chr(0x04) + chr(chan) + chr(lsb) + chr(msb)
        self.send(cmd)
        # Record Target value


    def set_target_vector(self, targets, sleep_time=0):
        for chan, pos in enumerate(targets):
            self.set_target(chan, pos)
        
        pause_sec = calculate_movement_time(get_max_angle(self.last_set_target_vector, targets))
        print(pause_sec)
        time.sleep(pause_sec)

        self.last_set_target_vector = targets
        # timeout = 5
        # while self.getMovingState(): #and time.time() - to < timeout:
        #     pass

    def run_trajectory(self, trajectory=trajectory):
        for new_target_vector in trajectory:
            self.set_target_vector(new_target_vector)
            
    # Set speed of channel
    # Speed is measured as 0.25microseconds/10milliseconds
    # For the standard 1ms pulse width change to move a servo between extremes, a speed
    # of 1 will take 1 minute, and a speed of 60 would take 1 second.
    # Speed of 0 is unrestricted.
    def setSpeed(self, chan, speed):
        lsb = speed & 0x7f  # 7 bits for least significant byte
        msb = (speed >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = chr(0x07) + chr(chan) + chr(lsb) + chr(msb)
        self.send(cmd)

    # Set acceleration of channel
    # This provide soft starts and finishes when servo moves to target position.
    # Valid values are from 0 to 255. 0=unrestricted, 1 is slowest start.
    # A value of 1 will take the servo about 3s to move between 1ms to 2ms range.
    def setAccel(self, chan, accel):
        lsb = accel & 0x7f  # 7 bits for least significant byte
        msb = (accel >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = chr(0x09) + chr(chan) + chr(lsb) + chr(msb)
        self.send(cmd)

    # Get the current position of the device on the specified channel
    # The result is returned in a measure of quarter-microseconds, which mirrors
    # the Target parameter of set_target.
    # This is not reading the true servo position, but the last target position sent
    # to the servo. If the Speed is set to below the top speed of the servo, then
    # the position result will align well with the acutal servo position, assuming
    # it is not stalled or slowed.
    def getPosition(self, chan):
        cmd = chr(0x10) + chr(chan)
        self.send(cmd)
        timeout = 1

        start_time = time.time()
        # your code

        while time.time() - start_time < timeout:
            if self.usb.in_waiting == 2:
                lsb = ord(self.usb.read())
                msb = ord(self.usb.read())
                return ((msb << 8) + lsb) / 4
        if time.time() - start_time > timeout:
            print('read timed out')
        return -1

    def get_all_positions(self):
        return [self.getPosition(x) in range(0, 5)]

    # Test to see if a servo has reached the set target position.  This only provides
    # useful results if the Speed parameter is set slower than the maximum speed of
    # the servo.  Servo range must be defined first using setRange. See setRange comment.
    #
    # ***Note if target position goes outside of Maestro's allowable range for the
    # channel, then the target can never be reached, so it will appear to always be
    # moving to the target.
    def isMoving(self, chan):
        if self.target_positions[chan] > 0:
            if abs(self.getPosition(chan) - self.target_positions[chan]) > 10:
                return 1
        return 0

    # Have all servo outputs reached their targets? This is useful only if Speed and/or
    # Acceleration have been set on one or more of the channels. Returns True or False.
    # Not available with Micro Maestro.
    def getMovingState(self):
        return sum([self.isMoving(x) for x in range(0, 5)])
        # Does not work on maestro6
        # cmd = chr(0x13)
        # self.send(cmd)
        # if self.read() == chr(0):
        #     return False
        # else:
        #     return True

    # Run a Maestro Script subroutine in the currently active script. Scripts can
    # have multiple subroutines, which get numbered sequentially from 0 on up. Code your
    # Maestro subroutine to either infinitely loop, or just end (return is not valid).
    def runScriptSub(self, subNumber):
        cmd = chr(0x27) + chr(subNumber)
        # can pass a param with command 0x28
        # cmd = chr(0x28) + chr(subNumber) + chr(lsb) + chr(msb)
        self.send(cmd)

    # Stop the current Maestro Script
    def stopScript(self):
        cmd = chr(0x24)
        self.send(cmd)

def get_max_angle(new_vector, old_vector):
    '''
    Determine maximum displace angle between current and the new position.    
    '''
    if len(new_vector) != len(old_vector):
        raise NameError("Input and output vectors must be the same length.")
    else:
        return max([abs(a-b) for a,b in zip(new_vector, old_vector)])

def calculate_movement_time(pwm_ms, speed_deg_per_sec=0):
    '''
    Calculate time to move the servo pwm increment.
    '''

    # TODO - read max/min pwm values and servo speed from a cal file.  The values will vary for different servos
    angle_0deg = 500
    angle_180deg = 2500    
    angular_speed_sec_per_degree = 0.2 / 60.0 # servo speed is typically quoted in sec per 60 deg and vary with voltage and load

    deg_per_ms = 180 / (angle_180deg - angle_0deg)
    travel_angle = (pwm_ms * deg_per_ms) 
    return travel_angle * angular_speed_sec_per_degree