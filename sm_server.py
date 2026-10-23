import asyncio
import c104
import concurrent.futures
import functools
import logging
import random
from datetime import datetime

single_point_value = {"state": False}

def async_exception_handler(task: asyncio.Future):
    try:
        task.result()
    except (asyncio.CancelledError, concurrent.futures.CancelledError):
        pass
    except Exception:
        logging.error(f"Unhandled exception in coroutine:", exc_info=True)


async def async_command(point: c104.Point):
    print(f"{point.type} DOUBLE COMMAND received on IOA: {point.io_address}, details: {point.info}")
    if isinstance(point.info, c104.DoubleCmd) and point.info.qualifier == c104.Qoc.LONG_PULSE:
        print("------> Received LONG PULSE")

    await asyncio.sleep(1)
    print("async_cmd: after sleep 1s")
    await asyncio.sleep(5)
    print("async_cmd: after sleep 5s")
    await asyncio.sleep(1)
    print("async_cmd: after sleep final 1s")

def on_setpoint_command(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage) -> c104.ResponseState:
    
    print("SV] {0} SETPOINT COMMAND on IOA: {1}, new: {2}, prev: {3}, cot: {4}, quality: {5}".format(point.type, point.io_address, point.value, previous_info, message.cot, point.quality))
    if point.related_io_address:
        print("SV] -> RELATED IO ADDRESS: {}".format(point.related_io_address))
        related_point = c104.get_point(point.related_io_address)
        if related_point:
            print("SV] -> RELATED POINT VALUE UPDATE")
            related_point.value = point.value
        else:
            print("SV] -> RELATED POINT NOT FOUND!")
    return c104.ResponseState.SUCCESS

def on_double_command(point: c104.Point, previous_info: c104.Information, message: c104.IncomingMessage,
                      loop: asyncio.AbstractEventLoop) -> c104.ResponseState:
    future = asyncio.run_coroutine_threadsafe(async_command(point), loop)
    future.add_done_callback(async_exception_handler)
    print("Value set to:", point.value)
    
    
    return c104.ResponseState.SUCCESS


def update_single_point(point: c104.Point) -> None:
    """Update single point (ON/OFF)"""
    point.value = single_point_value["state"]
def update_double_point(point: c104.Point) -> None:
    """Update double point (INDeterminate, OFF, ON)"""
    point.value = random.choice([c104.Double.INDETERMINATE, c104.Double.OFF, c104.Double.ON])
    point.info = c104.DoubleInfo(state=c104.Double.ON, quality=c104.Quality.Invalid, recorded_at=datetime.now())

def update_measured_value_normalized(point: c104.Point) -> None:
    """Update normalized measured value (-1.0 to 1.0)"""
    point.value =  random.random() * 100

def update_measured_value_scaled(point: c104.Point) -> None:
    """Update scaled measured value (integer)"""
    point.value =  random.random() * 100

def update_measured_value_short(point: c104.Point) -> None:
    """Update short floating point value"""
    point.value = random.random() * 100

def update_counter(point: c104.Point) -> None:
    """Update counter value"""
    point.value = random.randint(0, 65535)

def update_datetime(point: c104.Point) -> None:
    """Update datetime"""
    point.value = datetime.now()
def on_single_command(point: c104.Point, previous_info: c104.Information, 
                     message: c104.IncomingMessage) -> c104.ResponseState:
    single_point_value["state"] = point.value
    print(f"SINGLE COMMAND received on IOA: {point.io_address}")
    print(f"The value: {point.value}")
    print(f"Command info: {point.info}")
    
    if isinstance(point.info, c104.SingleCmd):
        if point.info.qualifier == c104.Qoc.SHORT_PULSE:
            print("------> Received SHORT PULSE SINGLE COMMAND")
        elif point.info.qualifier == c104.Qoc.LONG_PULSE:
            print("------> Received LONG PULSE SINGLE COMMAND")
    
    return c104.ResponseState.SUCCESS



async def main():
    loop = asyncio.get_event_loop()

    # --- Server Setup ---
    server = c104.Server()
    station = server.add_station(common_address=47)

    print("=== SETUP MONITORING POINTS ===")
    
    # --- Single Point Information ---
    sp_point = station.add_point(io_address=1, type=c104.Type.M_SP_NA_1, report_ms=5000)
    sp_point.on_before_auto_transmit(callable=update_single_point)
    sp_point.on_before_read(callable=update_single_point)
    print("Added Single Point (M_SP_NA_1) at IOA: 1")

    # --- Double Point Information ---
    dp_point = station.add_point(io_address=2, type=c104.Type.M_DP_NA_1, report_ms=5000)
    dp_point.on_before_auto_transmit(callable=update_double_point)
    dp_point.on_before_read(callable=update_double_point)
    print("Added Double Point (M_DP_NA_1) at IOA: 2")

    # --- Measured Value, Normalized ---
    norm_point = station.add_point(io_address=3, type=c104.Type.M_ME_NC_1, report_ms=7000)
    norm_point.on_before_auto_transmit(callable=update_measured_value_normalized)
    norm_point.on_before_read(callable=update_measured_value_normalized)
    print("Added Normalized Value (M_ME_NA_1) at IOA: 3")

    # --- Measured Value, Scaled ---
    scaled_point = station.add_point(io_address=4, type=c104.Type.M_ME_NC_1, report_ms=7000)
    scaled_point.on_before_auto_transmit(callable=update_measured_value_scaled)
    scaled_point.on_before_read(callable=update_measured_value_scaled)
    print("Added Scaled Value (M_ME_NB_1) at IOA: 4")

    # --- Measured Value, Short Floating Point ---
    short_point = station.add_point(io_address=11, type=c104.Type.M_ME_NC_1, report_ms=10000)
    short_point.on_before_auto_transmit(callable=update_measured_value_short)
    short_point.on_before_read(callable=update_measured_value_short)
    print("Added Short Float Value (M_ME_NC_1) at IOA: 11")

    sv_measurement_point = station.add_point(io_address=14, type=c104.Type.M_ME_NC_1, report_ms=1000)
    sv_measurement_point.value = 12.34
    sv_command_point = station.add_point(io_address=16, type=c104.Type.C_SE_NC_1, report_ms=0, related_io_address=sv_measurement_point.io_address, related_io_autoreturn=True, command_mode=c104.CommandMode.SELECT_AND_EXECUTE)
    sv_command_point.on_receive(callable=on_setpoint_command)

    # --- Integrated Totals (Counter) ---
    counter_point = station.add_point(io_address=15, type=c104.Type.M_IT_NA_1, report_ms=15000)
    counter_point.on_before_auto_transmit(callable=update_counter)
    counter_point.on_before_read(callable=update_counter)
    print("Added Counter (M_IT_NA_1) at IOA: 15")

    # --- Command Point Setup ---
    command = station.add_point(io_address=13, type=c104.Type.C_DC_TA_1)
    command.value = c104.Double.OFF
    command.on_receive(callable=functools.partial(on_double_command, loop=loop))
    print("Added Command Point (C_DC_TA_1) at IOA: 13")

    single_cmd_point = station.add_point(io_address=12, type=c104.Type.C_SC_NA_1)
    single_cmd_point.on_receive(callable=on_single_command)
    single_cmd_point.value = False  # Default OFF

    # --- Start the Server ---
    server.start()
    print("=== SERVER STARTED ===")

    # Wait until a client connects
    while not server.has_active_connections:
        print("Waiting for client connection...")
        await asyncio.sleep(1)

    print("Server running... Press Ctrl+C to stop")
    try:
        while server.has_open_connections:
            print("Server active - serving data...")
            await asyncio.sleep(120)  # Check setiap 30 detik
    except KeyboardInterrupt:
        print("Server stopped by user")
    finally:
        server.stop()

    forever = asyncio.Event()
    await forever.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())