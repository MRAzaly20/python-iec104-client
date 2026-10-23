# DCO Panel Redesign — Functional Double Command Control

Redesign the bottom-left "Double Command (DCO)" panel to be a **functional command control panel** for C_DC_TA_1 IOAs. The operator must select an IOA from the Data Points treeview before sending ON/OFF/INDETERMINATE/INTERMEDIATE commands.

## Proposed Changes

### IEC 104 Client GUI

#### [MODIFY] [client104.py](file:///c:/nexus-project/nexus-api/iiot_gateway_project/services/device_management/protocol/IEC104/example/read_write/agent/client104.py)

**1. Replace the static DCO panel (lines 1803–1848) with a new interactive command panel:**

The new panel will have:
- **Header**: "⚡ Double Command Control (C_DC_TA_1)"
- **Selected IOA indicator**: Shows currently selected IOA + variable name from the treeview, with a status badge showing whether the point is a valid command target
- **QOC Qualifier selector**: Dropdown with `No Pulse`, `Short Pulse`, `Long Pulse`, `Persistent` options
- **4 command buttons** in a 2×2 grid:
  - 🟢 **ON** (c104.Double.ON) — green accent
  - 🔴 **OFF** (c104.Double.OFF) — red accent
  - 🟡 **INDETERMINATE** (c104.Double.IND) — amber accent
  - 🔵 **INTERMEDIATE** (c104.Double.INT) — blue accent
- **Command status indicator**: Shows last command result

**2. Add treeview selection tracking:**

Bind the `<<TreeviewSelect>>` event on the main data grid (`self.tree`) to update the DCO panel's selected IOA display in real time. When a row is selected:
- Extract the IOA and TypeID from the selected row
- Display the IOA and variable name in the panel
- Enable/disable buttons based on whether the TypeID is `C_DC_TA_1`

**3. Add new method `send_dco_command(self, state_name)`:**

This method will:
1. Get the currently selected IOA from `self.tree`
2. Validate it's a `C_DC_TA_1` type point
3. Check it's registered in `self.monitoring_points`
4. Map the state name to `c104.Double` enum value
5. Get the selected QOC qualifier
6. Create `c104.DoubleCmd` with the state and qualifier
7. Queue the command via `self.command_queue`
8. Update the command status indicator

**4. Update [send_command_async](file:///c:/nexus-project/nexus-api/iiot_gateway_project/services/device_management/protocol/IEC104/example/read_write/agent/client104.py#3049-3077) to support all 4 DCS states:**

Currently only handles ON/OFF. Add INDETERMINATE and INTERMEDIATE:

```diff
-if state == "ON":
-    cmd_state = c104.Double.ON
-elif state == "OFF":
-    cmd_state = c104.Double.OFF
-else:
-    raise ValueError(f"Invalid command state: {state}")
+state_map = {
+    "ON": c104.Double.ON,
+    "OFF": c104.Double.OFF,
+    "INDETERMINATE": c104.Double.IND,
+    "INTERMEDIATE": c104.Double.INT,
+}
+cmd_state = state_map.get(state)
+if cmd_state is None:
+    raise ValueError(f"Invalid command state: {state}")
```

Also pass a `qualifier` parameter so the selected QOC is used:

```diff
-def send_command_async(self, command_point, state):
+def send_command_async(self, command_point, state, qualifier=None):
     ...
     command_point.info = c104.DoubleCmd(
         state=cmd_state,
-        qualifier=c104.Qoc.LONG_PULSE
+        qualifier=qualifier or c104.Qoc.LONG_PULSE
     )
```

**5. Update existing [send_on_command](file:///c:/nexus-project/nexus-api/iiot_gateway_project/services/device_management/protocol/IEC104/example/read_write/agent/client104.py#2926-2934) / [send_off_command](file:///c:/nexus-project/nexus-api/iiot_gateway_project/services/device_management/protocol/IEC104/example/read_write/agent/client104.py#2935-2943):**

These currently use [get_first_command_ioa()](file:///c:/nexus-project/nexus-api/iiot_gateway_project/services/device_management/protocol/IEC104/example/read_write/agent/client104.py#2917-2925). They will be updated to use the new selection-based approach through `send_dco_command`.

---

### UI Layout (New DCO Panel)

```
┌─────────────────────────────────────────────────────┐
│  ⚡ Double Command Control (C_DC_TA_1)              │
│                                                      │
│  ┌─ Selected Target ──────────────────────────────┐  │
│  │  IOA: 500        Name: Commands_1              │  │
│  │  Type: C_DC_TA_1          ● Ready              │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Qualifier: [Long Pulse ▾]                           │
│                                                      │
│  ┌──────────┐  ┌──────────┐                          │
│  │  ⬆  ON   │  │  ⬇  OFF  │                          │
│  └──────────┘  └──────────┘                          │
│  ┌──────────┐  ┌──────────┐                          │
│  │   IND    │  │   INT    │                          │
│  └──────────┘  └──────────┘                          │
│                                                      │
│  Last: ON → IOA 500 — SUCCESS                        │
└─────────────────────────────────────────────────────┘
```

## Verification Plan

### Manual Verification

1. **Launch**: Run `python client104.py` from `c:\nexus-project\...\agent\`
2. **Visual check**: Confirm the new DCO panel appears in the bottom-left with the 4 command buttons, selected IOA indicator, and qualifier dropdown
3. **Selection tracking**: Click different IOA rows in the Data Points grid and verify the panel updates the "Selected Target" section
4. **Type validation**: Select a monitoring IOA (e.g., M_SP_NA_1) and verify the buttons are disabled with a "Not a command point" indicator
5. **Command test** (requires IEC 104 server): Connect to a server, select a C_DC_TA_1 IOA, and click ON/OFF/IND/INT buttons — verify the command is logged
