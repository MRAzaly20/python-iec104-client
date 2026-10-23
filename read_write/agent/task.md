Phase 1: Testing Architecture & Code Structure Understanding
These questions verify if the Agent understands "how" the application is built.
 * "Can you generate a sequence diagram showing how a 'Connect' button click in the GUI eventually leads to a TCP connection being established in the background thread?"
 * "Explain the data flow when a new value arrives from the server. How does it travel from the c104 C++ callback to being displayed on the Tkinter Treeview?"
 * "Why do we need both message_queue and command_queue? What specific race conditions do they prevent?"
 * "Walk me through the StationConfig class. How does it handle the auto-generation of DataPoints, and what happens if two groups have overlapping IOAs?"
 * "How is the FlowControlManager integrated into the main client loop? What triggers it to stop?"
Phase 2: Testing Protocol Knowledge (IEC 60870-5-104)
These questions check if the Agent understands "what" the code is doing in relation to the standard.
 * "I see CP56Time2a class in the code. Why do we need to manually encode/decode bytes for time synchronization instead of just sending a string?"
 * "Explain the 'Select-Before-Operate' (SBO) logic implemented in CommandSender. Why is there a need for two separate request phases?"
 * "What is the purpose of the TESTFR (Test Frame) mechanism inside FlowControlManager, and how does the code handle a t1 timeout?"
 * "The code handles multiple ASDU types like M_SP_NA_1 and M_ME_NC_1. How does the application determine which Python data type (bool, float, int) to use for each?"
 * "In the write_point_async function, we see different 'Quality' flags being set (e.g., c104.Quality.Substituted). What does this flag mean in the context of SCADA?"
Phase 3: Testing Limitations & Robustness
These questions help you find bugs or missing features to work on next.
 * "Currently, the TimeSyncManager tries to sync time every hour. What happens if the network connection is lost right when the timer triggers?"
 * "If I try to send a command while the client is in the 'Reconnecting' state, what happens to that command? Is it queued, dropped, or does it throw an error?"
 * "The GUI uses root.after(100, self.process_queue) for polling. Is this efficient for high-frequency data (e.g., 1000 changes/second)? How might this impact the GUI responsiveness?"
 * "Look at the DataPoint class. It stores the value, but does it store the history of values? How would we implement a trend graph with the current data structure?"