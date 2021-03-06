########################################################################
#
# gantry_motors.py
#
# Motor class for the DPC gantry setup using EPICS package
#
# Author: Maria Buechner
#
# History:
# 25.02.2014: started
#
########################################################################


import epics
import logging
import controls.exceptions

logger = logging.getLogger(__name__)


class Motor():
    """ Class to define and control motors using the EPICS package
    """
    def __init__(
            self,
            epics_name,
            description,
            init=False,
            disabled=False,
            wait_for_finish=True):
        """ Initialization function, sets motor name and description and all
            other motor specific parameters

            Input variables:

                epics_name: Motor name in EPICS
                description: brief description
                init: if true, move to initialization position
                      (default: False)
                disabled: set the motor as disabled (default: False)
                wait_for_finish: wait for the motor finish movement
                before returning (default: True)

        """

        # Class variables
        # Init all Motor instances as false (enabled)
        self._motor_disabled = disabled
        # wait for processing to complete before returning
        self._wait_for_finish = wait_for_finish

        # Instance variables
        self._epics_name = epics_name
        self._description = description

        # Set motor process variable (PV)
        self._pv = epics.PV(self._epics_name + ".VAL")  # To set/get parameters

        self._val = self._pv.get()  # Current PV value

    def mv(self, absolute_position, timeout=9999):
        """ Move motor to absolute position

            Input parameters:

                absolute_position: absoulte "position" value, can be um/rad/V

            Return parameters:

                none

        """
        logger.debug("%s moving to absolute position %s",
                     self._epics_name,
                     absolute_position)
        if self._motor_disabled:
            raise controls.exceptions.MotorInterrupt(
                "Motor [{0}] is disabled".format(self._epics_name)
            )

        # Check validity of absolute position
        if (absolute_position > self._pv.upper_ctrl_limit
            or absolute_position < self._pv.lower_ctrl_limit):
            raise controls.exceptions.MotorInterrupt(
                "Moving motor [{0}] to position\
                [{1}] failed: position out of range.".format(
                    self._epics_name, absolute_position))

        # Set new position and wait (if necessary) for finish
        self._pv.put(absolute_position, self._wait_for_finish, timeout=timeout)

    def mvr(self, relative_position, timeout=9999):
        """ Move motor to relative position

            I.e. if current position is 40um, and mvr(20), move to 60um

            Input parameters:

                realtive_position: relative "position" value, can be um/rad/V

            Return parameters:

                none

        """
        logger.debug("%s moving relative %s",
                     self._epics_name,
                     relative_position)
        if self._motor_disabled:
            raise controls.exceptions.MotorInterrupt("Motor [{0}] is disabled"
                                 .format(self._epics_name))

        # Calculate absolute position
        absolute_position = self.get_current_value() + relative_position
        # Check validity of absolute position
        if (absolute_position > self._pv.upper_ctrl_limit
            or absolute_position < self._pv.lower_ctrl_limit):
            raise controls.exceptions.MotorInterrupt(
                "Moving motor [{0}] to position\
                [{1}] failed: position out of range.".format(
                    self._epics_name, absolute_position))

        # Set new position and wait (if necessary) for finish
        self._pv.put(absolute_position, self._wait_for_finish, timeout=timeout)

    # Get current value of motor PV (position)
    def get_current_value(self):
        """ Update motor PV value (position) and return it

            Input parameters:

                none

            Return parameters:

                self._val (current)

        """
        return self._pv.get()

    # Get high/low limits
    def get_high_limit(self):
        """ Return the motors high limit value

            Input parameters:

                none

            Return parameters:

                self._hlm

        """
        return self._pv.upper_ctrl_limit

    def get_low_limit(self):
        """ Return the motors low limit value

            Input parameters:

                none

            Return parameters:

                self._llm

        """
        return self._pv.lower_ctrl_limit

    # Print Info of single motor
    def __str__(self):
        """ Print epics name and description of motor
        """
        return "\n{0}\t\t{1}\t\t{2}".format(
            self._epics_name,
            self._description,
            self.get_current_value())
