"""
Telemetry gathering logic.
"""

import time
from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most recent attitude and position reading.
    """

    def __init__(
        self,
        time_since_boot: int | None = None,  # ms
        x: float | None = None,  # m
        y: float | None = None,  # m
        z: float | None = None,  # m
        x_velocity: float | None = None,  # m/s
        y_velocity: float | None = None,  # m/s
        z_velocity: float | None = None,  # m/s
        roll: float | None = None,  # rad
        pitch: float | None = None,  # rad
        yaw: float | None = None,  # rad
        roll_speed: float | None = None,  # rad/s
        pitch_speed: float | None = None,  # rad/s
        yaw_speed: float | None = None,  # rad/s
    ) -> None:
        self.time_since_boot = time_since_boot
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.z_velocity = z_velocity
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.roll_speed = roll_speed
        self.pitch_speed = pitch_speed
        self.yaw_speed = yaw_speed

    def __str__(self) -> str:
        return f"""{{
            time_since_boot: {self.time_since_boot},
            x: {self.x},
            y: {self.y},
            z: {self.z},
            x_velocity: {self.x_velocity},
            y_velocity: {self.y_velocity},
            z_velocity: {self.z_velocity},
            roll: {self.roll},
            pitch: {self.pitch},
            yaw: {self.yaw},
            roll_speed: {self.roll_speed},
            pitch_speed: {self.pitch_speed},
            yaw_speed: {self.yaw_speed}
        }}"""


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> "tuple[bool,Telemetry]|tuple[bool,None]":
        """
        Falliable create (instantiation) method to create a Telemetry object.
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
        :param local_logger: logger to log info and errors
        """
        assert key is Telemetry.__private_key, "Use create() method"
        self.connection = connection
        self.local_logger = local_logger
        local_logger.info("Initialized")
        self.attributes = {
            "time_last_attitude": 0,
            "time_last_local_position_ned": 0,
            "x": None,
            "y": None,
            "z": None,
            "vx": None,
            "vy": None,
            "vz": None,
            "pitch": None,
            "yaw": None,
            "roll": None,
            "rollspeed": None,
            "pitchspeed": None,
            "yawspeed": None,
        }
        self.times = {"attitude": 0, "position": 0}

    def run(
        self,
        # Put your own arguments here
    ) -> TelemetryData | None:
        """
        Docstring for run

        :param self: class object
        :return: Telemetry Data object with telemetry information
        """
        msg = self.connection.recv_match(
            type=["ATTITUDE", "LOCAL_POSITION_NED"], blocking=True, timeout=1 + 10e-2
        )
        telemetry_data = "Not Ready"
        if msg is not None:
            if msg.get_type() == "ATTITUDE":
                self.times["attitude"] = time.time()
                self.attributes["time_last_attitude"] = msg.time_boot_ms
                self.attributes["roll"] = msg.roll
                self.attributes["yaw"] = msg.yaw
                self.attributes["pitch"] = msg.pitch
                self.attributes["yawspeed"] = msg.yawspeed
                self.attributes["pitchspeed"] = msg.pitchspeed
                self.attributes["rollspeed"] = msg.rollspeed
            else:
                self.times["position"] = time.time()
                self.attributes["time_last_local_position_ned"] = msg.time_boot_ms
                self.attributes["x"] = msg.x
                self.attributes["y"] = msg.y
                self.attributes["z"] = msg.z
                self.attributes["vx"] = msg.vx
                self.attributes["vy"] = msg.vy
                self.attributes["vz"] = msg.vz
            if self.attributes["x"] is not None and self.attributes["roll"] is not None:
                if (
                    abs(
                        self.attributes["time_last_local_position_ned"]
                        - self.attributes["time_last_attitude"]
                    )
                    >= 1000
                ):
                    return None
                if (
                    time.time() - self.times["attitude"] > 1
                    or time.time() - self.times["position"] > 1
                ):
                    return None
                telemetry_data = TelemetryData(
                    max(
                        self.attributes["time_last_local_position_ned"],
                        self.attributes["time_last_attitude"],
                    ),
                    self.attributes["x"],
                    self.attributes["y"],
                    self.attributes["z"],
                    self.attributes["vx"],
                    self.attributes["vy"],
                    self.attributes["vz"],
                    self.attributes["roll"],
                    self.attributes["pitch"],
                    self.attributes["yaw"],
                    self.attributes["rollspeed"],
                    self.attributes["pitchspeed"],
                    self.attributes["yawspeed"],
                )
                for index in self.attributes:
                    self.attributes[index] = None
        else:
            telemetry_data = None
            for index in self.attributes:
                self.attributes[index] = None
        return telemetry_data
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
