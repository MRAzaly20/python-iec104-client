import asyncio
import c104
import concurrent.futures
import functools
import logging
import random
from datetime import datetime


# State management untuk menyimpan nilai yang diterima dari client
class ServerState:
    def __init__(self):
        self.point_values = {
            1: False,           # IOA 1 - Single Point
            2: c104.Double.OFF, # IOA 2 - Double Point  
            3: 0.0,             # IOA 3 - Normalized Value
            4: 0,               # IOA 4 - Scaled Value
            11: 0.0,            # IOA 11 - Short Float Value
            15: 0,              # IOA 15 - Counter
            13: c104.Double.OFF # IOA 13 - Command
        }

server_state = ServerState()


def async_exception_handler(task: asyncio.Future):
    try:
        task.result()
    except (asyncio.CancelledError, concurrent.futures.CancelledError):
        pass
    except Exception:
        logging.error(f"Unhandled exception in coroutine:", exc_info=True)


async def async_command(point: c104.Point):
    print(f"{point.type} COMMAND received on IOA: {point.io_address}, details: {point.info}")
    if isinstance(point.info, c104.DoubleCmd) and point.info.qualifier == c104.Qoc.LONG_PULSE:
        print("------> Received LONG PULSE")

    await asyncio.sleep(1)
    print("async_cmd: after sleep 1s")
    await asyncio.sleep(5)
    print("async_cmd: after sleep 5s")
    await asyncio.sleep(1)
    print("async_cmd: after sleep final 1s")


# Handler untuk setiap tipe command
def on_single_point_command(point: c104.Point, previous_info: c104.Information, 
                          message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Single Point (IOA 1)"""
    try:
        if hasattr(point.info, 'value'):
            server_state.point_values[1] = point.info.value
            print(f"IOA 1 - Single Point updated to: {point.info.value}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 1 command: {e}")
        return c104.ResponseState.FAILURE


def on_double_point_command(point: c104.Point, previous_info: c104.Information, 
                           message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Double Point (IOA 2)"""
    try:
        if hasattr(point.info, 'value'):
            server_state.point_values[2] = point.info.value
            print(f"IOA 2 - Double Point updated to: {point.info.value}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 2 command: {e}")
        return c104.ResponseState.FAILURE


def on_normalized_command(point: c104.Point, previous_info: c104.Information, 
                         message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Normalized Value (IOA 3)"""
    try:
        if hasattr(point.info, 'value'):
            # Clamp to valid range
            value = max(-1.0, min(1.0, point.info.value))
            server_state.point_values[3] = value
            print(f"IOA 3 - Normalized Value updated to: {value}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 3 command: {e}")
        return c104.ResponseState.FAILURE


def on_scaled_command(point: c104.Point, previous_info: c104.Information, 
                     message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Scaled Value (IOA 4)"""
    try:
        if hasattr(point.info, 'value'):
            # Clamp to valid range
            value = max(-32768, min(32767, int(point.info.value)))
            server_state.point_values[4] = value
            print(f"IOA 4 - Scaled Value updated to: {value}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 4 command: {e}")
        return c104.ResponseState.FAILURE


def on_short_float_command(point: c104.Point, previous_info: c104.Information, 
                          message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Short Float Value (IOA 11)"""
    try:
        if hasattr(point.info, 'value'):
            server_state.point_values[11] = float(point.info.value)
            print(f"IOA 11 - Short Float Value updated to: {point.info.value}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 11 command: {e}")
        return c104.ResponseState.FAILURE


def on_counter_command(point: c104.Point, previous_info: c104.Information, 
                      message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Counter (IOA 15)"""
    try:
        if hasattr(point.info, 'value'):
            # Ensure positive value
            value = max(0, int(point.info.value))
            server_state.point_values[15] = value
            print(f"IOA 15 - Counter updated to: {value}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 15 command: {e}")
        return c104.ResponseState.FAILURE


def on_double_command(point: c104.Point, previous_info: c104.Information, 
                     message: c104.IncomingMessage) -> c104.ResponseState:
    """Handle command untuk Command Point (IOA 13)"""
    try:
        if isinstance(point.info, c104.DoubleCmd):
            server_state.point_values[13] = point.info.state
            print(f"IOA 13 - Command received: {point.info.state}")
            
        future = asyncio.run_coroutine_threadsafe(async_command(point), asyncio.get_event_loop())
        future.add_done_callback(async_exception_handler)
        return c104.ResponseState.SUCCESS
    except Exception as e:
        print(f"Error handling IOA 13 command: {e}")
        return c104.ResponseState.FAILURE


# Update functions yang menggunakan state yang diterima dari client
def update_single_point(point: c104.Point) -> None:
    """Update single point dengan nilai dari client atau random"""
    try:
        # Gunakan nilai dari client jika tersedia, jika tidak gunakan random
        if 1 in server_state.point_values:
            value = server_state.point_values[1]
        else:
            value = random.choice([True, False])
            
        point.info = c104.SingleInfo(on=True, quality=c104.Quality.Invalid, recorded_at=datetime.now())
        print(f"IOA 1 transmitting: {value}")
    except Exception as e:
        print(f"Error updating IOA 1: {e}")
        point.info = c104.SingleInfo(
            value=False,
            quality=c104.Quality(is_good=False, invalid=True)
        )


def update_double_point(point: c104.Point) -> None:
    """Update double point dengan nilai dari client atau random"""
    try:
        if 2 in server_state.point_values:
            value = server_state.point_values[2]
        else:
            value = random.choice([c104.Double.IND, c104.Double.OFF, c104.Double.ON])
            
        point.info = c104.DoubleInfo(
            value=value,
            quality=c104.Quality.GOOD
        )
        print(f"IOA 2 transmitting: {value}")
    except Exception as e:
        print(f"Error updating IOA 2: {e}")
        point.info = c104.DoubleInfo(
            value=c104.Double.IND,
            quality=c104.Quality(is_good=False, invalid=True)
        )


def update_measured_value_normalized(point: c104.Point) -> None:
    """Update normalized measured value dengan nilai dari client atau random"""
    try:
        if 3 in server_state.point_values:
            value = max(-1.0, min(1.0, server_state.point_values[3]))
        else:
            value = random.uniform(-1.0, 1.0)
            
        point.info = c104.ScaledInfo(
            value=value,
            quality=c104.Quality.GOOD
        )
        print(f"IOA 3 transmitting: {value:.3f}")
    except Exception as e:
        print(f"Error updating IOA 3: {e}")
        point.info = c104.ScaledInfo(
            value=0.0,
            quality=c104.Quality(is_good=False, invalid=True)
        )


def update_measured_value_scaled(point: c104.Point) -> None:
    """Update scaled measured value dengan nilai dari client atau random"""
    try:
        if 4 in server_state.point_values:
            value = max(-32768, min(32767, server_state.point_values[4]))
        else:
            value = random.randint(-32768, 32767)
            
        point.info = c104.ScaledInfo(
            value=value,
            quality=c104.Quality.GOOD
        )
        print(f"IOA 4 transmitting: {value}")
    except Exception as e:
        print(f"Error updating IOA 4: {e}")
        point.info = c104.ScaledInfo(
            value=0,
            quality=c104.Quality(is_good=False, invalid=True)
        )


def update_measured_value_short(point: c104.Point) -> None:
    """Update short floating point value dengan nilai dari client atau random"""
    try:
        if 11 in server_state.point_values:
            value = server_state.point_values[11]
        else:
            value = random.random() * 100
            
        point.info = c104.Int16(
            value=value,
            quality=c104.Quality.GOOD
        )
        print(f"IOA 11 transmitting: {value:.2f}")
    except Exception as e:
        print(f"Error updating IOA 11: {e}")
        point.info = c104.ShortInfo(
            value=0.0,
            quality=c104.Quality(is_good=False, invalid=True)
        )


def update_counter(point: c104.Point) -> None:
    """Update counter value dengan nilai dari client atau random"""
    try:
        if 15 in server_state.point_values:
            value = max(0, server_state.point_values[15])
        else:
            value = random.randint(0, 65535)
            
        point.info = c104.Int16(
            value=value,
            quality=c104.Quality.GOOD
        )
        print(f"IOA 15 transmitting: {value}")
    except Exception as e:
        print(f"Error updating IOA 15: {e}")
        point.info = c104.Int16(
            value=0,
            quality=c104.Quality(is_good=False, invalid=True)
        )


async def main():
    # --- Server Setup ---
    server = c104.Server()
    station = server.add_station(common_address=47)

    print("=== SETUP MONITORING POINTS ===")
    
    # --- Single Point Information (IOA: 1) ---
    sp_point = station.add_point(io_address=1, type=c104.Type.M_SP_NA_1, report_ms=5000)
    sp_point.on_before_auto_transmit(callable=update_single_point)
    sp_point.on_before_read(callable=update_single_point)
    sp_point.on_receive(callable=on_single_point_command)  # ← Tambahkan ini
    print("Added Single Point (M_SP_NA_1) at IOA: 1")

    # --- Double Point Information (IOA: 2) ---
    dp_point = station.add_point(io_address=2, type=c104.Type.M_DP_NA_1, report_ms=5000)
    dp_point.on_before_auto_transmit(callable=update_double_point)
    dp_point.on_before_read(callable=update_double_point)
    dp_point.on_receive(callable=on_double_point_command)  # ← Tambahkan ini
    print("Added Double Point (M_DP_NA_1) at IOA: 2")

    # --- Measured Value, Normalized (IOA: 3) ---
    norm_point = station.add_point(io_address=3, type=c104.Type.M_ME_NA_1, report_ms=7000)  # ← FIXED type
    norm_point.on_before_auto_transmit(callable=update_measured_value_normalized)
    norm_point.on_before_read(callable=update_measured_value_normalized)
    norm_point.on_receive(callable=on_normalized_command)  # ← Tambahkan ini
    print("Added Normalized Value (M_ME_NA_1) at IOA: 3")

    # --- Measured Value, Scaled (IOA: 4) ---
    scaled_point = station.add_point(io_address=4, type=c104.Type.M_ME_NB_1, report_ms=7000)  # ← FIXED type
    scaled_point.on_before_auto_transmit(callable=update_measured_value_scaled)
    scaled_point.on_before_read(callable=update_measured_value_scaled)
    scaled_point.on_receive(callable=on_scaled_command)  # ← Tambahkan ini
    print("Added Scaled Value (M_ME_NB_1) at IOA: 4")

    # --- Measured Value, Short Floating Point (IOA: 11) ---
    short_point = station.add_point(io_address=11, type=c104.Type.M_ME_NC_1, report_ms=10000)
    short_point.on_before_auto_transmit(callable=update_measured_value_short)
    short_point.on_before_read(callable=update_measured_value_short)
    short_point.on_receive(callable=on_short_float_command)  # ← Tambahkan ini
    print("Added Short Float Value (M_ME_NC_1) at IOA: 11")

    # --- Integrated Totals (Counter) (IOA: 15) ---
    counter_point = station.add_point(io_address=15, type=c104.Type.M_IT_NA_1, report_ms=15000)
    counter_point.on_before_auto_transmit(callable=update_counter)
    counter_point.on_before_read(callable=update_counter)
    counter_point.on_receive(callable=on_counter_command)  # ← Tambahkan ini
    print("Added Counter (M_IT_NA_1) at IOA: 15")

    # --- Command Point Setup (IOA: 13) ---
    command = station.add_point(io_address=13, type=c104.Type.C_DC_TA_1)
    command.info = c104.DoubleCmd(
        state=c104.Double.OFF,
        qualifier=c104.Qoc.LONG_PULSE
    )
    command.on_receive(callable=on_double_command)
    print("Added Command Point (C_DC_TA_1) at IOA: 13")

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
            await asyncio.sleep(30)  # Check setiap 30 detik
    except KeyboardInterrupt:
        print("Server stopped by user")
    finally:
        server.stop()

    forever = asyncio.Event()
    await forever.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())