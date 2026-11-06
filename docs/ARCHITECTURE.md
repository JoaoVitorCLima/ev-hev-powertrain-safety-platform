# Architecture and limitations

1. **MATLAB** models a simplified vehicle, producing CSV telemetry. A separate optional **Python** source produces deterministic synthetic data with injected faults.
2. **Virtual CAN** is modeled by Python encoder/decoder functions, with arbitrary development-only IDs 0x180 and 0x200 and an alive counter. This is **not** a live CAN network, SocketCAN interface, or authentic manufacturer DBC.
3. **C++17 supervisor** consumes the decoded telemetry CSV and outputs `NORMAL`, `DERATED`, or latched `FAULT` plus an allowed **positive** torque request. Limits are illustrative and are not qualified for a production vehicle.
4. **Python validation** checks that faulted frames command zero positive traction torque and produces a standalone HTML report. The simulator is intentionally simple and has not been safety certified.

## Safety concept (demonstration only)

| Detection | Condition | Mode | Response in simulation |
|---|---|---|---|
| Battery temperature high | >= 48 C | DERATED | Limit positive torque to 60 Nm |
| Battery temperature critical | >= 60 C | FAULT | Positive torque request becomes 0 Nm |
| Battery SOC low | < 15% | DERATED | Limit positive torque to 60 Nm |
| Battery current high | > 200 A abs | DERATED | Limit positive torque to 60 Nm |
| Battery current critical | >= 300 A abs | FAULT | Positive torque request becomes 0 Nm |
| CAN message overdue | > 100 ms | FAULT | Positive torque request becomes 0 Nm |
| Counter discontinuity | modulo-16 error | FAULT | Positive torque request becomes 0 Nm |

FAULT is latched until process restart in this proof of concept. Production systems require carefully specified reset criteria, redundancies, diagnostic coverage, safety requirements, and extensive validation. This toy supervisor is not suitable for real vehicle actuation.

## Future stages (not implemented)

- Detailed Simulink motor/inverter plant, battery/BMS and BEV/series-HEV powerflow (a simple BEV closed-loop `.slx` model is already included).
- Automotive CAN via Virtual CAN/SocketCAN, CAN FD, DBC, capture, timeout model, and fault injection.
- SIL/HIL test orchestration, code coverage, requirements traceability.
- Sensor validation, plausible torque arbitration, thermal derating curves and safe-state design.
- Security mechanisms such as authentication and anti-replay (a four-bit rolling counter is **not** cryptographic authentication).

No claim of compliance with ISO 26262, ISO/SAE 21434, or a road-legal electrical safety standard is made.
