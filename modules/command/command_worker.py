"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    queue_input: queue_proxy_wrapper.QueueProxyWrapper,
    queue_output: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
    # Add other necessary worker arguments here
) -> None:
    """
    Docstring for command_worker

    :param connection: mavlink communication object
    :param target: position object as 3d vector
    :param queue_input: input queue to recieve data
    :param queue_output: output queue to send data
    :param controller: controller object
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
    # Instantiate class object (command.Command)
    success, command_obj = command.Command.create(connection, local_logger)
    if not success:
        local_logger.error("Could not create command object")
    assert command_obj is not None
    queue_info = None
    while not controller.is_exit_requested():
        controller.check_pause()
        data = queue_input.queue.get()
        if data is None:
            continue
        queue_info = command_obj.run(data, target)
        if queue_info is not None:
            queue_output.queue.put(queue_info)

    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
