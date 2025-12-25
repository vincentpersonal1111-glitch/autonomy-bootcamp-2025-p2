"""
Heartbeat sending logic.
"""

import time
from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        mav_type: int,
        autopilot: int,
        base_mode: int,
        custom_mode: int,
        system_status: int,
    ) -> "tuple[bool,HeartbeatSender] | tuple[bool, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if connection is None:
            return False, None
        return True, HeartbeatSender(
            cls.__private_key,
            connection,
            mav_type,
            autopilot,
            base_mode,
            custom_mode,
            system_status,
        )  # Create a HeartbeatSender object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        mav_type: int,
        autopilot: int,
        base_mode: int,
        custom_mode: int,
        system_status: int,
    ) -> None:
        """
        Docstring for __init__

        :param self: class object
        :param key: key from create method
        :param connection: mavlink communication object
        :param mav_type: Type of the MAV
        :param autopilot: Autopilot type
        :param base_mode: System mode bitmap.
        :param custom_mode: A bitfield for use for autopilot-specific flag
        :param system_status: System status flag
        """

        assert key is HeartbeatSender.__private_key, "Use create() method"

        self.connection = connection
        self.mav_type = mav_type
        self.autopilot = autopilot
        self.base_mode = base_mode
        self.custom_mode = custom_mode
        self.system_status = system_status

    def run(
        self,
    ) -> float:
        """
        Docstring for run

        :param self: class object
        :return: time for debugging
        """
        self.connection.mav.heartbeat_send(
            self.mav_type, self.autopilot, self.base_mode, self.custom_mode, self.system_status
        )
        return time.time()


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
