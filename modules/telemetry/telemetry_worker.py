"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import telemetry
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def telemetry_worker(
    connection: mavutil.mavfile,
    queue: queue_proxy_wrapper.QueueProxyWrapper,  # Place your own arguments here
    controller: worker_controller.WorkerController,
    # Add other necessary worker arguments here
) -> None:
    """
    Docstring for telemetry_worker

    :param connection: connection object
    :param controller: controller object
    :param queue: output queue
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
    # Instantiate class object (telemetry.Telemetry)
    success, telemetry_obj = telemetry.Telemetry.create(connection, local_logger)
    if not success:
        local_logger.error("Could not create telemetry object")
    assert telemetry_obj is not None
    while not controller.is_exit_requested():
        controller.check_pause()
        data = telemetry_obj.run()
        if data is not None and data != "Not Ready":
            queue.queue.put(data)
            local_logger.info("Recieved telemetry data")
        elif data is None:
            local_logger.info("timeout")
    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
