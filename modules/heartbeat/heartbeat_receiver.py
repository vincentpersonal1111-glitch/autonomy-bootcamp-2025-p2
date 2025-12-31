"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> "tuple[True,HeartbeatReceiver]|tuple[False,None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if connection is None:
            return False, None
        return True, cls(cls.__private_key, connection, local_logger)

    def __init__(
        self, key: object, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> None:
        """
        Docstring for __init__

        :param self: class object
        :param key: key from .create method
        :param connection: mavlink communication object
        :param local_logger: logger to log data and warnings
        """
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self.connection = connection
        self.local_logger = local_logger
        self.count = 0

        # Do any intializiation here

    def run(self, timeout: float) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        recieved = self.connection.wait_heartbeat(blocking=True, timeout=timeout)
        if recieved is None:
            self.local_logger.warning("Heartbeat not detected")
            self.count += 1
        else:
            self.count = 0
            self.local_logger.info("Heartbeat detected")
        if self.count >= 5:
            return "Disconnected"
        return "Connected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
