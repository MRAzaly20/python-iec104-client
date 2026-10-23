import asyncio
import c104
import concurrent.futures
import functools
import logging


def async_exception_handler(task: asyncio.Future):
    try:
        task.result()
    except (asyncio.CancelledError, concurrent.futures.CancelledError):
        return
    except Exception:
        logging.error(f"Unhandled exception in coroutine:", exc_info=True)


async def async_measurement(point: c104.Point, message: c104.IncomingMessage) -> None:
    print(f"{point.type} MEASUREMENT received on IOA: {point.io_address}")
    print(f"  Value: {point.value}")
    print(f"  Info: {point.info}")
    
    await asyncio.sleep(1)  # Simulate processing delay
    print(f"  Processing completed for IOA: {point.io_address}")


def on_receive_point(point: c104.Point, previous_info: c104.Information,
                     message: c104.IncomingMessage, loop: asyncio.AbstractEventLoop) -> c104.ResponseState:
    future = asyncio.run_coroutine_threadsafe(async_measurement(point, message), loop)
    future.add_done_callback(async_exception_handler)
    return c104.ResponseState.SUCCESS


async def read_all_points(points_dict):
    """Fungsi untuk membaca semua point"""
    print("\n=== READING ALL POINTS ===")
    for name, point in points_dict.items():
        print(f"Reading {name} (IOA: {point.io_address})...")
        if point.read():
            print(f"  -> SUCCESS: {name} = {point.value}")
        else:
            print(f"  -> FAILED: {name}")
        await asyncio.sleep(0.5)  # Delay antar pembacaan


async def main():
    loop = asyncio.get_event_loop()

    # --- Client Setup ---
    client = c104.Client()
    connection = client.add_connection(ip="127.0.0.1", port=2404, init=c104.Init.ALL)
    station = connection.add_station(common_address=47)

    print("=== SETUP MONITORING POINTS ===")
    
    # Dictionary untuk menyimpan semua point
    monitoring_points = {}
    
    # --- Single Point Information ---
    sp_point = station.add_point(io_address=1, type=c104.Type.M_SP_NA_1)
    sp_point.on_receive(callable=functools.partial(on_receive_point, loop=loop))
    monitoring_points["Single Point"] = sp_point
    print("Added Single Point (M_SP_NA_1) at IOA: 1")


    # --- Double Point Information ---
    dp_point = station.add_point(io_address=2, type=c104.Type.M_DP_NA_1)
    dp_point.on_receive(callable=functools.partial(on_receive_point, loop=loop))
    monitoring_points["Double Point"] = dp_point
    print("Added Double Point (M_DP_NA_1) at IOA: 2")

    # --- Measured Value, Normalized ---
    norm_point = station.add_point(io_address=3, type=c104.Type.M_ME_NA_1)
    norm_point.on_receive(callable=functools.partial(on_receive_point, loop=loop))
    monitoring_points["Normalized Value"] = norm_point
    print("Added Normalized Value (M_ME_NA_1) at IOA: 3")

    # --- Measured Value, Scaled ---
    scaled_point = station.add_point(io_address=4, type=c104.Type.M_ME_NB_1)
    scaled_point.on_receive(callable=functools.partial(on_receive_point, loop=loop))
    monitoring_points["Scaled Value"] = scaled_point
    print("Added Scaled Value (M_ME_NB_1) at IOA: 4")

    # --- Measured Value, Short Floating Point ---
    short_point = station.add_point(io_address=11, type=c104.Type.M_ME_NC_1)
    short_point.on_receive(callable=functools.partial(on_receive_point, loop=loop))
    monitoring_points["Short Float Value"] = short_point
    print("Added Short Float Value (M_ME_NC_1) at IOA: 11")

    # --- Integrated Totals (Counter) ---
    counter_point = station.add_point(io_address=15, type=c104.Type.M_IT_NA_1)
    counter_point.on_receive(callable=functools.partial(on_receive_point, loop=loop))
    monitoring_points["Counter"] = counter_point
    print("Added Counter (M_IT_NA_1) at IOA: 15")

    # --- Command Point Setup ---
    command = station.add_point(io_address=13, type=c104.Type.C_DC_TA_1)
    print("Added Command Point (C_DC_TA_1) at IOA: 13")

    # --- Start the Client ---
    client.start()

    while connection.state != c104.ConnectionState.OPEN:
        print(f"Waiting for connection to {connection.ip}:{connection.port}...")
        await asyncio.sleep(1)

    print(f"Client connected.")
    
    # --- Initial Read All Points ---
    print("Client running... Press Ctrl+C to stop")
    try:
        while connection.state == c104.ConnectionState.OPEN:
            print("Client active - monitoring data...")
            await asyncio.sleep(30)  # Check setiap 30 detik
    except KeyboardInterrupt:
        print("Client stopped by user")
    finally:
        client.stop()

    # --- Transmit a Double Command ---
    print("\n=== TRANSMITTING COMMAND ===")
    print("Triggering double command...")
    command.info = c104.DoubleCmd(state=c104.Double.ON, qualifier=c104.Qoc.LONG_PULSE)
    if command.transmit(cause=c104.Cot.ACTIVATION):
        print("-> Command SUCCESS")
    else:
        print("-> Command FAILURE")

    # --- Keep Alive to Process Incoming Data ---
    print("\n=== MONITORING AUTO UPDATES ===")
    forever = asyncio.Event()
    await forever.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())