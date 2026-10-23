import asyncio
import c104
import concurrent.futures
import functools
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import queue

class IEC104ClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("IEC 60870-5-104 Client Monitor")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Threading variables
        self.message_queue = queue.Queue()
        self.command_queue = queue.Queue()
        
        # Data storage
        self.points_data = {}
        self.connection_status = "DISCONNECTED"
        
        # Setup GUI
        self.setup_gui()
        
        # Start IEC 104 client
        self.start_iec104_client()
        
        # Start queue processor
        self.process_queue()
        
    def setup_gui(self):
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="IEC 60870-5-104 Client Monitor", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Connection Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="Connection Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Status: DISCONNECTED", 
                                     font=('Arial', 12, 'bold'))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.last_update_label = ttk.Label(status_frame, text="Last Update: -")
        self.last_update_label.grid(row=1, column=0, sticky=tk.W)
        
        # Points Display Frame
        points_frame = ttk.LabelFrame(main_frame, text="Monitoring Points", padding="10")
        points_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        points_frame.columnconfigure(0, weight=1)
        points_frame.rowconfigure(0, weight=1)
        
        # Create Treeview for points
        columns = ('IOA', 'Type', 'Description', 'Value', 'Quality', 'Timestamp')
        self.tree = ttk.Treeview(points_frame, columns=columns, show='tree headings', height=12)
        
        # Define headings
        self.tree.heading('IOA', text='IOA')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Description', text='Description')
        self.tree.heading('Value', text='Value')
        self.tree.heading('Quality', text='Quality')
        self.tree.heading('Timestamp', text='Timestamp')
        
        # Define column widths
        self.tree.column('IOA', width=60, anchor='center')
        self.tree.column('Type', width=150, anchor='center')
        self.tree.column('Description', width=150)
        self.tree.column('Value', width=120, anchor='center')
        self.tree.column('Quality', width=100, anchor='center')
        self.tree.column('Timestamp', width=200, anchor='center')
        
        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(points_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(points_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Initialize tree with point definitions
        self.initialize_points_tree()
        
        # Command Frame
        command_frame = ttk.LabelFrame(main_frame, text="Commands", padding="10")
        command_frame.grid(row=2, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        command_frame.columnconfigure(0, weight=1)
        ttk.Label(command_frame, text="IOA 12 - Single Command:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20, 10))

        # Single Command buttons
        single_button_frame = ttk.Frame(command_frame)
        single_button_frame.pack(fill=tk.X, pady=5)

        self.single_on_button = ttk.Button(single_button_frame, text="SINGLE ON", 
                                          command=lambda: self.send_single_command_gui("ON"))
        self.single_on_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.single_off_button = ttk.Button(single_button_frame, text="SINGLE OFF", 
                                          command=lambda: self.send_single_command_gui("OFF"))
        self.single_off_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(command_frame, text="IOA 13 - Double Command:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # Command buttons
        button_frame = ttk.Frame(command_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.on_button = ttk.Button(button_frame, text="ON", command=self.send_on_command)
        self.on_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.off_button = ttk.Button(button_frame, text="OFF", command=self.send_off_command)
        self.off_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Command status
        self.command_status = ttk.Label(command_frame, text="", foreground="blue")
        self.command_status.pack(anchor=tk.W, pady=(10, 0))
        
        # Read Points Button
        self.read_button = ttk.Button(command_frame, text="Read All Points", command=self.read_all_points_gui)
        self.read_button.pack(fill=tk.X, pady=(20, 0))
        
        # Statistics Frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="Points Received: 0 | Connection Time: 0s")
        self.stats_label.pack(anchor=tk.W)
        
        # Log Frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add tags for coloring
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("COMMAND", foreground="blue")
        
    def initialize_points_tree(self):
        """Initialize tree with point definitions"""
        point_definitions = [
            (1, 'M_SP_NA_1', 'Single Point', '-', 'UNKNOWN', '-'),
            (2, 'M_DP_NA_1', 'Double Point', '-', 'UNKNOWN', '-'),
            (3, 'M_ME_NA_1', 'Normalized Value', '-', 'UNKNOWN', '-'),
            (4, 'M_ME_NB_1', 'Scaled Value', '-', 'UNKNOWN', '-'),
            (11, 'M_ME_NC_1', 'Short Float Value', '-', 'UNKNOWN', '-'),
            (15, 'M_IT_NA_1', 'Counter', '-', 'UNKNOWN', '-'),
            (13, 'C_DC_TA_1', 'Double Command', 'COMMAND', 'N/A', '-'),
            (12, 'C_SC_NA_1', 'Single Command', '-', 'UNKNOWN', '-')
        ]
        
        for ioa, type_name, desc, value, quality, timestamp in point_definitions:
            item_id = f"point_{ioa}"
            self.tree.insert('', 'end', iid=item_id, values=(ioa, type_name, desc, value, quality, timestamp))
            self.points_data[ioa] = {
                'type': type_name,
                'description': desc,
                'value': value,
                'quality': quality,
                'timestamp': timestamp,
                'count': 0
            }
    
    def update_point_display(self, ioa, value, quality, timestamp):
        """Update point display in GUI"""
        item_id = f"point_{ioa}"
        if item_id in self.tree.get_children():
            self.tree.item(item_id, values=(ioa, self.points_data[ioa]['type'], 
                                          self.points_data[ioa]['description'], 
                                          str(value), str(quality), timestamp))
            
            # Update data storage
            self.points_data[ioa].update({
                'value': value,
                'quality': quality,
                'timestamp': timestamp,
                'count': self.points_data[ioa].get('count', 0) + 1
            })
            
            # Update statistics
            self.update_statistics()
    def send_single_command_gui(self, state):
        """Send single command via GUI"""
        self.command_queue.put(("SINGLE_COMMAND", state))
        self.command_status.config(text=f"Sending SINGLE {state} command...", foreground="orange")
        self.log_message(f"Sending SINGLE {state} command to IOA 12...", "COMMAND")
    def update_connection_status(self, status, details=""):
        """Update connection status display"""
        self.connection_status = status
        status_text = f"Status: {status}"
        if details:
            status_text += f" - {details}"
            
        self.status_label.config(text=status_text)
        
        # Update color based on status
        if status == "CONNECTED":
            self.status_label.config(foreground="green")
        elif status == "CONNECTING":
            self.status_label.config(foreground="orange")
        else:
            self.status_label.config(foreground="red")
            
        self.last_update_label.config(text=f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def update_statistics(self):
        """Update statistics display"""
        total_points = sum(self.points_data[ioa].get('count', 0) for ioa in self.points_data if ioa != 13)
        self.stats_label.config(text=f"Points Received: {total_points}")
    
    def log_message(self, message, level="INFO"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to queue for thread-safe processing
        self.message_queue.put((formatted_message, level))
    
    def send_on_command(self):
        """Send ON command"""
        self.command_queue.put(("COMMAND", "ON"))
        self.command_status.config(text="Sending ON command...", foreground="orange")
        self.log_message("Sending ON command to IOA 13...", "COMMAND")

    def send_off_command(self):
        """Send OFF command"""
        self.command_queue.put(("COMMAND", "OFF"))
        self.command_status.config(text="Sending OFF command...", foreground="orange")
        self.log_message("Sending OFF command to IOA 13...", "COMMAND")

    # Dan dalam fungsi iec104_client_main, ubah bagian command processing:
    # Process commands
    
    
    def read_all_points_gui(self):
        """Read all points"""
        self.command_queue.put(("READ_ALL",))
        self.log_message("Reading all points...", "COMMAND")
    
    def start_iec104_client(self):
        """Start IEC 104 client in separate thread"""
        client_thread = threading.Thread(target=self.run_iec104_client, daemon=True)
        client_thread.start()
    
    def process_queue(self):
        """Process message queue"""
        try:
            # Process messages
            while not self.message_queue.empty():
                message, level = self.message_queue.get_nowait()
                self.log_text.insert(tk.END, message, level)
                self.log_text.see(tk.END)
                self.log_text.update()
            
            # Process commands
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                if command[0] == "ON":
                    self.command_status.config(text="ON command sent", foreground="green")
                elif command[0] == "OFF":
                    self.command_status.config(text="OFF command sent", foreground="green")
                elif command[0] == "READ_ALL":
                    self.command_status.config(text="Reading points...", foreground="blue")
                    
        except queue.Empty:
            pass
        
        # Schedule next queue processing
        self.root.after(100, self.process_queue)
    
    def async_exception_handler(self, task: asyncio.Future):
        try:
            task.result()
        except (asyncio.CancelledError, concurrent.futures.CancelledError):
            return
        except Exception as e:
            self.log_message(f"Error in async task: {str(e)}", "ERROR")
            logging.error(f"Unhandled exception in coroutine:", exc_info=True)
    
    async def async_measurement(self, point: c104.Point, message: c104.IncomingMessage) -> None:
        """Handle incoming measurements"""
        try:
            # Extract value
            if hasattr(point.info, 'value'):
                value = point.info.value
            else:
                value = getattr(point, 'value', 'N/A')
                
            # Extract quality
            if hasattr(point.info, 'quality'):
                quality = "GOOD" if point.info.quality.is_good else "BAD"
            else:
                quality = "UNKNOWN"
                
            # Extract timestamp
            if hasattr(point.info, 'processed_at') and point.info.processed_at:
                timestamp = point.info.processed_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Queue update for GUI thread
            self.message_queue.put((f"Received {point.type} on IOA {point.io_address}: {value}\n", "SUCCESS"))
            
            # Update GUI from main thread
            self.root.after(0, self.update_point_display, point.io_address, value, quality, timestamp)
            
        except Exception as e:
            self.message_queue.put((f"Error processing point {point.io_address}: {str(e)}\n", "ERROR"))
    
    def on_receive_point(self, point: c104.Point, previous_info: c104.Information,
                        message: c104.IncomingMessage, loop: asyncio.AbstractEventLoop) -> c104.ResponseState:
        """Synchronous callback for point reception"""
        try:
            future = asyncio.run_coroutine_threadsafe(self.async_measurement(point, message), loop)
            future.add_done_callback(self.async_exception_handler)
        except Exception as e:
            self.root.after(0, self.log_message, f"Error in receive callback: {str(e)}", "ERROR")
        
        return c104.ResponseState.SUCCESS
    async def send_single_command_async(self, command_point, state):
      """Send single command to server"""
      try:
          # Konversi state ke boolean
          if isinstance(state, str):
              cmd_value = state.upper() == "ON"
          else:
              cmd_value = bool(state)
          
          # Buat SingleCmd info
          command_info = c104.SingleCmd(
              on=cmd_value,
              qualifier=c104.Qoc.SHORT_PULSE  # atau LONG_PULSE
          )
          
          # Set command info ke point
          command_point.info = command_info
          
          # Kirim command
          if command_point.transmit(cause=c104.Cot.ACTIVATION):
              self.root.after(0, self.log_message, f"Single command {'ON' if cmd_value else 'OFF'} sent successfully", "SUCCESS")
              self.root.after(0, lambda: self.command_status.config(text=f"Single command {'ON' if cmd_value else 'OFF'} SUCCESS", foreground="green"))
          else:
              self.root.after(0, self.log_message, f"Failed to send single command {'ON' if cmd_value else 'OFF'}", "ERROR")
              self.root.after(0, lambda: self.command_status.config(text=f"Single command FAILED", foreground="red"))
              
      except Exception as e:
          self.root.after(0, self.log_message, f"Error sending single command: {str(e)}", "ERROR")
          self.root.after(0, lambda: self.command_status.config(text=f"Single command ERROR", foreground="red"))
    async def send_command_async(self, command_point, state):
      """Send command to server"""
      try:
          # Perbaikan: Akses enum dengan benar
          if state == "ON":
              cmd_state = c104.Double.ON
          elif state == "OFF":
              cmd_state = c104.Double.OFF
          else:
              raise ValueError(f"Invalid command state: {state}")
          
          # Buat command info
          command_point.info = c104.DoubleCmd(
              state=cmd_state,
              qualifier=c104.Qoc.SHORT_PULSE
          )
          
          # Kirim command
          if command_point.transmit(cause=c104.Cot.ACTIVATION):
              self.root.after(0, self.log_message, f"{state} command sent successfully", "SUCCESS")
              self.root.after(0, lambda: self.command_status.config(text=f"{state} command SUCCESS", foreground="green"))
          else:
              self.root.after(0, self.log_message, f"Failed to send {state} command", "ERROR")
              self.root.after(0, lambda: self.command_status.config(text=f"{state} command FAILED", foreground="red"))
              
      except Exception as e:
          self.root.after(0, self.log_message, f"Error sending {state} command: {str(e)}", "ERROR")
          self.root.after(0, lambda: self.command_status.config(text=f"{state} command ERROR", foreground="red"))
    async def read_all_points_async(self, points_dict):
        """Read all points"""
        try:
            self.root.after(0, self.log_message, "Reading all points...", "COMMAND")
            
            for name, point in points_dict.items():
                if point.read():
                    self.root.after(0, self.log_message, f"Read SUCCESS: {name} = {point.value}", "SUCCESS")
                else:
                    self.root.after(0, self.log_message, f"Read FAILED: {name}", "ERROR")
                await asyncio.sleep(0.1)
                
            self.root.after(0, lambda: self.command_status.config(text="Read completed", foreground="green"))
            
        except Exception as e:
            self.root.after(0, self.log_message, f"Error reading points: {str(e)}", "ERROR")
    
    async def iec104_client_main(self):
        """Main IEC 104 client logic"""
        loop = asyncio.get_event_loop()
        
        try:
            # --- Client Setup ---
            client = c104.Client()
            connection = client.add_connection(ip="127.0.0.1", port=2404, init=c104.Init.ALL)
            station = connection.add_station(common_address=47)
            
            # Update GUI status
            self.root.after(0, self.update_connection_status, "CONNECTING")
            self.root.after(0, self.log_message, "Starting IEC 104 client...")
            
            # Dictionary untuk menyimpan semua point
            monitoring_points = {}
            
            # --- Setup Points ---
            # Single Point Information
            sp_point = station.add_point(io_address=1, type=c104.Type.M_SP_NA_1)
            sp_point.on_receive(callable=functools.partial(self.on_receive_point, loop=loop))
            monitoring_points["Single Point"] = sp_point
            
            # Double Point Information
            dp_point = station.add_point(io_address=2, type=c104.Type.M_DP_NA_1)
            dp_point.on_receive(callable=functools.partial(self.on_receive_point, loop=loop))
            monitoring_points["Double Point"] = dp_point
            
            # Measured Value, Normalized
            norm_point = station.add_point(io_address=3, type=c104.Type.M_ME_NC_1)
            norm_point.on_receive(callable=functools.partial(self.on_receive_point, loop=loop))
            monitoring_points["Normalized Value"] = norm_point
            
            # Measured Value, Scaled
            scaled_point = station.add_point(io_address=4, type=c104.Type.M_ME_NC_1)
            scaled_point.on_receive(callable=functools.partial(self.on_receive_point, loop=loop))
            #scaled_point.value = 12.3456
            monitoring_points["Scaled Value"] = scaled_point
            
            # Measured Value, Short Floating Point
            short_point = station.add_point(io_address=11, type=c104.Type.M_ME_NC_1)
            short_point.on_receive(callable=functools.partial(self.on_receive_point, loop=loop))
            monitoring_points["Short Float Value"] = short_point
            
            # Integrated Totals (Counter)
            counter_point = station.add_point(io_address=15, type=c104.Type.M_IT_NA_1)
            counter_point.on_receive(callable=functools.partial(self.on_receive_point, loop=loop))
            monitoring_points["Counter"] = counter_point
            
            # Command Point Setup
            command = station.add_point(io_address=13, type=c104.Type.C_DC_TA_1)
            single_command = station.add_point(io_address=12, type=c104.Type.C_SC_NA_1)
            
            # --- Start Client ---
            client.start()
            
            # Wait for connection
            while connection.state != c104.ConnectionState.OPEN:
                await asyncio.sleep(0.5)
            
            # Update GUI status
            self.root.after(0, self.update_connection_status, "CONNECTED")
            self.root.after(0, self.log_message, "Connected to IEC 104 server")
            
            # Process commands
            while connection.state == c104.ConnectionState.OPEN:
              # Check for commands
              try:
                  if not self.command_queue.empty():
                      cmd = self.command_queue.get_nowait()
                      if cmd[0] == "COMMAND":
                          state = cmd[1]  # "ON" atau "OFF" untuk DoubleCmd
                          await self.send_command_async(command, state)
                      elif cmd[0] == "SINGLE_COMMAND":
                          state = cmd[1]  # "ON" atau "OFF" untuk SingleCmd
                          await self.send_single_command_async(single_command, state)
                      elif cmd[0] == "READ_ALL":
                          await self.read_all_points_async(monitoring_points)
              except queue.Empty:
                  pass
              
              await asyncio.sleep(0.1)
                
            # Connection lost
            self.root.after(0, self.update_connection_status, "DISCONNECTED")
            self.root.after(0, self.log_message, "Connection to server lost")
            
        except Exception as e:
            self.root.after(0, self.log_message, f"IEC 104 client error: {str(e)}", "ERROR")
            self.root.after(0, self.update_connection_status, "ERROR", str(e))
    
    def run_iec104_client(self):
        """Run IEC 104 client in separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.iec104_client_main())
    
    def run(self):
        """Start the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        self.log_message("Application closing...", "INFO")
        self.root.destroy()

# Main execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create and run GUI
    app = IEC104ClientGUI()
    app.run()