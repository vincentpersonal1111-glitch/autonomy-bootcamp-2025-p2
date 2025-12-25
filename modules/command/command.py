"""
Decision-making logic.
"""

import math
import time
from pymavlink import mavutil
from utilities.workers import queue_proxy_wrapper
from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> "tuple[bool,Command]|tuple[bool,None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if connection is None:
            return False, None
        return True, cls(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        """
        Docstring for __init__

        :param self: class object
        :param key: key from create method
        :param connection: mavlink communication object
        :param local_logger: Logger to log data and warnings
        """
        assert key is Command.__private_key, "Use create() method"
        self.connection = connection
        self.local_logger = local_logger
        self.velocity_sum = [0, 0, 0]
        self.time = time.time()
        self.i = 1

    def run(
        self,
        data: telemetry.TelemetryData,
        target: Position,
        queue: queue_proxy_wrapper.QueueProxyWrapper,
    ) -> None:
        """
        Docstring for run
        Make a decision based on received telemetry data.

        :param self: class object
        :param data: Telemetry data object
        :param target: Target position object vector
        :param queue: output queue to log commands
        """
        turn_angle = 0
        self.velocity_sum[0] += data.x_velocity
        self.velocity_sum[1] += data.y_velocity
        self.velocity_sum[2] += data.z_velocity
        self.local_logger.info(
            f"Recieved {data}, Average velocity {[self.velocity_sum[0]/self.i,self.velocity_sum[1]/self.i,self.velocity_sum[2]/self.i]}"
        )
        self.i += 1
        if abs(target.z - data.z) > 0.5:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                data.z + (target.z - data.z),
            )
            queue.queue.put(f"CHANGE ALTITUDE: {target.z-data.z}")
        else:
            deltax = target.x - data.x
            deltay = target.y - data.y
            current_yaw = data.yaw*180/math.pi
            try:
                angle = math.atan2(abs(deltay), abs(deltax))*180/math.pi
                if deltay >= 0:
                    turn_angle = -current_yaw + angle
                    if deltax <= 0:
                        turn_angle = turn_angle + 180 - 2 * angle
                if deltay <= 0:
                    turn_angle = -current_yaw - angle
                    if deltax <= 0:
                        turn_angle = turn_angle - 180 + 2 * angle
            except ZeroDivisionError:
                turn_angle = -current_yaw
                if deltay > 0:
                    turn_angle = turn_angle + 90
                else:
                    turn_angle = turn_angle - 90
            if turn_angle > 180:
                turn_angle -= 360
            if turn_angle < -180:
                turn_angle += 360
            if turn_angle<0:
                direction=1
            else:
                direction=-1
            if abs(turn_angle) > 5:
                self.connection.mav.command_long_send(
                    1, 0, mavutil.mavlink.MAV_CMD_CONDITION_YAW, 0, abs(turn_angle), 5, direction, 1, 0, 0, 0
                )
                queue.queue.put(f"CHANGE YAW: {turn_angle}")

        # Log average velocity for this trip so far

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
