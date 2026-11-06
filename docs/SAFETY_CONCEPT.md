# Research-level safety concept (not an ISO 26262 safety case)

## Boundaries

- Simulator-only and **not for a road vehicle**; no qualified software, independent redundancy, contactor actuation, torque plausibility validation, or automotive-safe shutdown.
- Modes: `NORMAL`, `DERATED`, `FAULT` (fault latch until ECU process reset). `FAULT` commands zero motor torque in the simulated plant; this is **not equivalent to a safe stop**.
- Nominal current limit 200 A for derating, 300 A fault. Battery temp ≥48 °C derate, ≥60 °C fault; SOC below 15% derate. All illustrative.
- CAN timeout >100 ms or invalid modulo-16 counter faults. The counter is **not** a security authenticator; this project does not implement cryptographic protection.

## Preliminary hazard reasoning

| Hazard | Possible cause | Implemented prototype response | Missing for production |
|---|---|---|---|
| Unintended torque | Stale VCU command or malformed telemetry | Reject with fault latch | ASIL analysis, diverse monitor, brake coordination |
| Excessive battery temperature | Thermal fault | Zero torque request | Thermal propagation and pack contactor strategy |
| Excessive current | Inverter or sensor problem | Zero torque request | Redundant sensing, contactor coordination |
| Loss of CAN | Missing messages | Zero torque request | Safe state per vehicle speed/road context |
| Low SOC | Battery nearly depleted | Limit positive/negative torque | Real BMS voltage/SoH limits, regen constraints |

**No compliance claim** is made for ISO 26262, ISO/SAE 21434, ISO 6469, UNECE R155/R156 or other regulations.
