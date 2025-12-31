"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_sender_worker(
    connection: mavutil.mavfile,
    mav_type: int,
    autopilot: int,
    base_mode: int,
    custom_mode: int,
    system_status: int,
    controller: worker_controller.WorkerController,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.
    mav_type          : Type of the MAV (quadrotor, helicopter, etc.) (type:uint8_t, values:MAV_TYPE)
    autopilot         : Autopilot type / class. (type:uint8_t, values:MAV_AUTOPILOT)
    base_mode         : System mode bitmap. (type:uint8_t, values:MAV_MODE_FLAG)
    custom_mode       : A bitfield for use for autopilot-specific flags (type:uint32_t)
    system_status     : System status flag. (type:uint8_t, values:MAV_STATE)
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (heartbeat_sender.HeartbeatSender)

    # Main loop: do work.
    success, sender = heartbeat_sender.HeartbeatSender.create(
        connection, mav_type, autopilot, base_mode, custom_mode, system_status
    )
    if not success:
        local_logger.error("Couldn't create heartbeat sender object")
    assert sender is not None
    while not controller.is_exit_requested():
        controller.check_pause()
        now = sender.run()
        time.sleep(1)
        local_logger.info(f"Sent Heartbeat {time.time()-now}")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
