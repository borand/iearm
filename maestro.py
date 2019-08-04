import serial
import time
import json
from sys import version_info
import os
import logging

PY2 = version_info[0] == 2  # Running Python 2.x?

logger = logging.getLogger('maestro')
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)12s - %(levelname)10s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# create file handler which logs even debug messages
# fh = logging.FileHandler('maestro.log')
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(formatter)
# logger.addHandler(fh)


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

DEFAULT_CONFIG = {
    'min': [500, 500, 500, 500, 500, 500],
    'max': [2500, 2500, 2500, 2500, 2500, 2500],
    'home': [1500, 1500, 1500, 1500, 1500, 1500],
    'speed': [0, 0, 0, 0, 0, 0],
    'accel': [0, 0, 0, 0, 0, 0],
    'delay_adjust' : 1,
    'num_of_channels' : 5
}

def load_config_file(filename="maestro.json"):
    """
    Loads config file in json format and returns config dictionary
    """
    if os.path.isfile(filename):
        try:
            fid = open(filename,'r')
            out = fid.read()
            fid.close()
            config = json.loads(out)
            return config
        except:            
            logger.error("cannot decode maestro config.json file - using DEFAULT_CONFIG")
            
    else:
        logger.error("cannot find maestro config.json file in the directory - using DEFAULT_CONFIG")
    return DEFAULT_CONFIG

class Controller:
    """
    When connected via USB, the Maestro creates two virtual serial ports
    /dev/ttyACM0 for commands and /dev/ttyACM1 for communications.
    Be sure the Maestro is configured for "USB Dual Port" serial mode.
    "USB Chained Mode" may work as well, but hasn't been tested.
    
    Pololu protocol allows for multiple Maestros to be connected to a single
    serial port. Each connected device is then indexed by number.
    This device number defaults to 0x0C (or 12 in decimal), which this module
    assumes.  If two or more controllers are connected to different serial
    ports, or you are using a Windows OS, you can provide the tty port.  For
    example, '/dev/ttyACM2' or for Windows, something like 'COM3'.
    """
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

        # Track target position for each servo. The function is_moving() will
        # use the Target vs Current servo position to determine if movement is
        # occuring.  Upto 24 servos on a Maestro, (0-23). target_positions start at 0.
        self.target_positions = [0] * 24
        # Servo minimum and maximum targets can be restricted to protect components.
        self.Mins = [0] * 24
        self.Maxs = [0] * 24
        
        logger.info("Controller(tty_str={}, device={})".format(self.tty_str, device))

        self.establish_connection()
        
        if not self.tty_port_connection_established:
            logger.error("Did not establish connection during object initialization")
        else:
            logger.info("Connection established")

    def __del__(self):
        self.save_config_file()

    def establish_connection(self):
        logger.debug("Attempting to establish connection with: {}".format(self.tty_str))
        try:
            if os.path.exists(self.tty_str):
                logger.debug("Found {} on the path".format(self.tty_str))
                self.usb = serial.Serial(self.tty_str, timeout=1)
                self.tty_port_exists = True
                
                self.config = load_config_file()
                self.last_set_target_vector = self.get_all_positions()
                
                # Set speed of all channels from the config file
                for s in enumerate(self.config['speed']):
                    self.set_speed(s[0], s[1])

                self.tty_port_connection_established = True
            else:
                logger.error('Specified serial port does not exist')
        except Exception as e:
            self.last_exception = e
            logger.error("Cannot connect to the controller. last_exception = {}".format(e))
    
    def reload_default_config(self, filename="maestro.json"):
        self.config = load_config_file()
    
    def save_config_file(self, fileanme="last_maestro_config.json"):
        """
        Save current configuration to file for future usage.
        """
        logger.info('Saving current config as: {}'.format(fileanme))
        try: 
            fid = open(fileanme,'w')
            fid.write(json.dumps(self.config))
        except Exception as e:
            logger.error(e)

    def close(self):
        """ Cleanup by closing USB serial port"""
        if self.tty_port_connection_established:
            self.usb.close()
    
    def send(self, cmd):
        """ Send a Pololu command out the serial port """ 
        self.last_cmd_send = cmd        
        if self.establish_connection:
            cmd_str = self.pololu_cmd + cmd
            if PY2:
                out = self.usb.write(cmd_str)
            else:
                out = self.usb.write(bytes(cmd_str, 'latin-1'))
            # logger.debug("send({})".format(out))
        else:
            logger.warning("Cannot send command connection is not established")
            out = -1
        return out

    def read(self):
        """ Read a Pololu response """ 
        response = -1
        if self.establish_connection:
            if self.usb.is_open:
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    if self.usb.in_waiting == 1:
                        response = ord(self.usb.read())
                        logger.debug("read() = {}".format(response))
            else:
                logger.warning("Cannot use read command when the port is closed")
        else:
            logger.warning("Cannot use read command when connection is not established")
        return response
   
    def set_range(self, chan, min, max):
        """ Set channels min and max value range.  Use this as a safety to protect
        from accidentally moving outside known safe parameters. A setting of 0
        allows unrestricted movement.
        
        ***Note that the Maestro itself is configured to limit the range of servo travel
        which has precedence over these values.  Use the Maestro Control Center to configure
        ranges that are saved to the controller.  Use set_range for software controllable ranges.
        """
        if chan >=0 and chan <=24:
            self.Mins[chan] = min
            self.Maxs[chan] = max
        else:
            logger.error("Specified channel is out of range")
    
    def get_min(self, chan):
        """ Return Minimum channel range value"""
        return self.Mins[chan]

    def getMax(self, chan):
        """ Return Maximum channel range value """
        return self.Maxs[chan]

    def set_target(self, chan: object, target: object) -> object:
        """
        Set channel to a specified target value.  Servo will begin moving based
        on Speed and Acceleration parameters previously set.
        Target values will be constrained within Min and Max range, if set.
        For servos, target represents the pulse width in of quarter-microseconds
        Servo center is at 1500 microseconds, or 6000 quarter-microseconds
        Typcially valid servo range is 3000 to 9000 quarter-microseconds
        If channel is configured for digital output, values < 6000 = Low ouput
        """
        self.target_positions[chan] = target
        target = round(target * 4)
        # if Min is defined and Target is below, force to Min
        if self.Mins[chan] > 0 and target < self.Mins[chan]:
            target = self.Mins[chan]
        
        # if Max is defined and Target is above, force to Max
        if self.Maxs[chan] > 0 and target > self.Maxs[chan]:
            target = self.Maxs[chan]
        
        lsb = target & 0x7f  # 7 bits for least significant byte
        msb = (target >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = chr(0x04) + chr(chan) + chr(lsb) + chr(msb)
        self.send(cmd)
        # Record Target value

    def set_target_vector(self, targets, sleep_time=0):
        for chan, pos in enumerate(targets):
            self.set_target(chan, pos)
        
        pause_sec = self.get_slowest_movement_time(self.last_set_target_vector)
        logger.debug("set_target_vector pause time: {}".format(pause_sec))
        time.sleep(pause_sec)

        self.last_set_target_vector = targets
        # timeout = 5
        # while self.getMovingState(): #and time.time() - to < timeout:
        #     pass

    def run_trajectory(self, trajectory):
        for new_target_vector in trajectory:
            self.set_target_vector(new_target_vector)
   
    def set_speed(self, chan, speed):
        """
        Set speed of channel
        Speed is measured as 0.25microseconds/10milliseconds
        For the standard 1ms pulse width change to move a servo between extremes, a speed
        of 1 will take 1 minute, and a speed of 60 would take 1 second.
        Speed of 0 is unrestricted.
        """
        lsb = speed & 0x7f  # 7 bits for least significant byte
        msb = (speed >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = chr(0x07) + chr(chan) + chr(lsb) + chr(msb)
        self.send(cmd)
        self.config['speed'][chan] = speed

    def set_accel(self, chan, accel):
        """
        Set acceleration of channel
        This provide soft starts and finishes when servo moves to target position.
        Valid values are from 0 to 255. 0=unrestricted, 1 is slowest start.
        A value of 1 will take the servo about 3s to move between 1ms to 2ms range.
        """
        lsb = accel & 0x7f  # 7 bits for least significant byte
        msb = (accel >> 7) & 0x7f  # shift 7 and take next 7 bits for msb
        cmd = chr(0x09) + chr(chan) + chr(lsb) + chr(msb)
        self.send(cmd)

    def get_position(self, chan):
        """
        Get the current position of the device on the specified channel
        The result is returned in a measure of quarter-microseconds, which mirrors
        the Target parameter of set_target.
        This is not reading the true servo position, but the last target position sent
        to the servo. If the Speed is set to below the top speed of the servo, then
        the position result will align well with the acutal servo position, assuming
        it is not stalled or slowed.
        """
        response = -1
        if self.tty_port_connection_established:
            cmd = chr(0x10) + chr(chan)
            self.send(cmd)
            self.timeout = 1
            start_time = time.time()
            while time.time() - start_time < self.timeout:
                if self.usb.in_waiting == 2:
                    lsb = ord(self.usb.read())
                    msb = ord(self.usb.read())
                    return ((msb << 8) + lsb) / 4
            if time.time() - start_time > self.timeout:
                print('read timed out')
        
        return response

    def get_all_positions(self):
        return [self.get_position(x) for x in range(0, self.config['num_of_channels'])]
    
    def is_moving(self, chan):
        """
        Test to see if a servo has reached the set target position.  This only provides
        useful results if the Speed parameter is set slower than the maximum speed of
        the servo.  Servo range must be defined first using set_range. See set_range comment.
        
        ***Note if target position goes outside of Maestro's allowable range for the
        channel, then the target can never be reached, so it will appear to always be
        moving to the target.
        """
        if self.target_positions[chan] > 0:
            if abs(self.get_position(chan) - self.target_positions[chan]) > 10:
                return 1
        return 0
    
    def get_moving_state(self):
        """
        Have all servo outputs reached their targets? This is useful only if Speed and/or
        Acceleration have been set on one or more of the channels. Returns True or False.
        Not available with Micro Maestro.
        """
        return sum([self.is_moving(x) for x in range(0, 5)])
        # Does not work on maestro6
        # cmd = chr(0x13)
        # self.send(cmd)
        # if self.read() == chr(0):
        #     return False
        # else:
        #     return True
    
    def run_scriptSub(self, subNumber):
        """
        Run a Maestro Script subroutine in the currently active script. Scripts can
        have multiple subroutines, which get numbered sequentially from 0 on up. Code your
        Maestro subroutine to either infinitely loop, or just end (return is not valid).
        """
        cmd = chr(0x27) + chr(subNumber)
        # can pass a param with command 0x28
        # cmd = chr(0x28) + chr(subNumber) + chr(lsb) + chr(msb)
        self.send(cmd)
    
    def stop_script(self):
        """
        Stop the current Maestro Script
        """
        cmd = chr(0x24)
        self.send(cmd)

    def get_max_angle(self, new_vector):
        '''
        Determine maximum displace angle between current and the new position.    
        '''
        old_vector=self.last_set_target_vector
        if len(new_vector) != len(old_vector):
            raise NameError("Input and output vectors must be the same length.")
        else:
            return max([abs(a-b) for a,b in zip(new_vector, old_vector)])

    def calculate_movement_time(self, pwm_ms, speed_deg_per_sec=0):
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

    def get_slowest_movement_time(self, new_vector):
        old_vector = self.last_set_target_vector
        speed = self.config['speed']
        speed_us_per_ms = [ 0.25 * v / 10.0 for v in speed]
        delta_pwm_us = [abs(a-b) for a,b in zip(new_vector, old_vector)]
        slowest_movement_at_speed =  self.config['delay_adjust'] * max([s*t for s,t in zip(speed_us_per_ms, delta_pwm_us)]) / 1000.0
        slowest_movement_at_speed_0 = self.calculate_movement_time(self.get_max_angle(new_vector))
        logger.debug("slowest_movement_at_speed={}, slowest_movement_at_speed_0={}".format(slowest_movement_at_speed, slowest_movement_at_speed_0))
        return max([slowest_movement_at_speed, slowest_movement_at_speed_0])

    