"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import time

from pymavlink import mavutil

from modules.common.modules.logger import logger
from modules.common.modules.logger import logger_main_setup
from modules.common.modules.read_yaml import read_yaml
from modules.command import command
from modules.command import command_worker
from modules.heartbeat import heartbeat_receiver_worker
from modules.heartbeat import heartbeat_sender_worker
from modules.telemetry import telemetry_worker
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from utilities.workers import worker_manager


# MAVLink connection
CONNECTION_STRING = "tcp:localhost:12345"

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# Set queue max sizes (<= 0 for infinity)
QUEUE_MAX_SIZE = 1
# Set worker counts
WORKER_COUNT = 1

# Any other constants

# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


def main() -> int:
    """
    Main function.
    """
    # Configuration settings
    result, config = read_yaml.open_config(logger.CONFIG_FILE_PATH)
    if not result:
        print("ERROR: Failed to load configuration file")
        return -1

    # Get Pylance to stop complaining
    assert config is not None

    # Setup main logger
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1

    # Get Pylance to stop complaining
    assert main_logger is not None

    # Create a connection to the drone. Assume that this is safe to pass around to all processes
    # In reality, this will not work, but to simplify the bootamp, preetend it is allowed
    # To test, you will run each of your workers individually to see if they work
    # (test "drones" are provided for you test your workers)
    # NOTE: If you want to have type annotations for the connection, it is of type mavutil.mavfile
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat(timeout=30)  # Wait for the "drone" to connect

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Create a worker controller
    controller = worker_controller.WorkerController()
    # Create a multiprocess manager for synchronized queues
    mp_manager = mp.Manager()
    # Create queues
    heartbeat_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, QUEUE_MAX_SIZE)
    telemetry_data_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, QUEUE_MAX_SIZE)
    command_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, QUEUE_MAX_SIZE)
    # Create worker properties for each worker type (what inputs it takes, how many workers)
    heartbeat_sender_properties = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        heartbeat_sender_worker.heartbeat_sender_worker,
        (mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_TYPE_INVALID, 0, 0, 0),
        [],
        [],
        controller,
        main_logger,
    )
    heartbeat_reciever_properties = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        heartbeat_receiver_worker.heartbeat_receiver_worker,
        (connection,),
        [],
        [heartbeat_queue],
        controller,
        main_logger,
    )
    telemetry_worker_properties = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        telemetry_worker.telemetry_worker,
        (connection,),
        [],
        [telemetry_data_queue],
        controller,
        main_logger,
    )
    command_worker_properties = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        command_worker.command_worker,
        (connection, command.Position(10, 20, 30)),
        [telemetry_data_queue],
        [command_queue],
        controller,
        main_logger,
    )

    # Heartbeat sender

    # Heartbeat receiver

    # Telemetry

    # Command

    # Create the workers (processes) and obtain their managers
    _, heartbeat_sender_manager = worker_manager.WorkerManager.create(
        heartbeat_sender_properties, main_logger
    )
    _, heartbeat_receiver_manager = worker_manager.WorkerManager.create(
        heartbeat_reciever_properties, main_logger
    )
    _, telemetry_manager = worker_manager.WorkerManager.create(
        telemetry_worker_properties, main_logger
    )
    _, command_manager = worker_manager.WorkerManager.create(command_worker_properties, main_logger)
    # Start worker processes
    heartbeat_sender_manager.start_workers()
    heartbeat_receiver_manager.start_workers()
    telemetry_manager.start_workers()
    command_manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    now = time.time()
    while time.time() - now < 100:
        connected = heartbeat_queue.queue.get()
        main_logger.info(connected)
        if connected == "Disconnected":
            break
        main_logger.info(command_queue.queue.get())

    main_logger.info("Requested exit")
    controller.request_exit()
    # Fill and drain queues from END TO START
    command_queue.fill_and_drain_queue()
    heartbeat_queue.fill_and_drain_queue()
    telemetry_data_queue.fill_and_drain_queue()
    main_logger.info("Queues cleared")
    # Clean up worker processes
    heartbeat_receiver_manager.join_workers()
    heartbeat_sender_manager.join_workers()
    telemetry_manager.join_workers()
    command_manager.join_workers()

    main_logger.info("Stopped")
    # We can reset controller in case we want to reuse it
    controller.clear_exit()
    # Alternatively, create a new WorkerController instance

    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    return 0


if __name__ == "__main__":
    result_main = main()
    if result_main < 0:
        print(f"Failed with return code {result_main}")
    else:
        print("Success!")
