# EV/HEV Powertrain Simulation and Safety Validation Platform

**C++17 safety supervisor · Python closed-loop SIL · MATLAB/Simulink examples · virtual CAN · BEV and series-HEV**

> **Scope:** Original, synthetic engineering portfolio prototype; **not a vehicle-ready controller, certified functional safety system, or hardware-in-the-loop bench**. BEV and HEV models are intentionally low-fidelity. No production tuning data, vendor CAN database or proprietary tool binaries are included.

## Implemented and verified

| Capability | Implementation | Verification |
|---|---|---|
| C++17 safety controller | State-aware `NORMAL`/`DERATED`/latched `FAULT`; torque limitation, CAN freshness/counter, battery limits | Automated native builds, tests |
| Python↔C++ **closed-loop SIL** | Persistent request-response with C++ (one time-step at a time) and feedback torque into Python vehicle dynamics | Automated regression and scenarios |
| Electric vehicle | Longitudinal vehicle dynamics, velocity PI + anti-windup, simplified battery SOC/thermal, limited regen | Python end-to-end integration tests |
| Series hybrid vehicle | Electric traction + simplified on/off SOC-controlled genset, battery SOC and estimated fuel use | Python end-to-end integration tests |
| CAN-like virtual network | BMS status and VCU torque payload encoders/decoders with project-defined IDs and rolling counter | Automated codec, counter and timeout tests |
| Failures | Nominal, overtemperature, overcurrent, low SOC, CAN timeout and bad counter | Regression tests |
| Reporting | CSV for full traces, dependency-free HTML plots | Demonstration generated locally |
| MATLAB model | Simplified BEV simulation and offline CSV bridge to C++ | Executed by project author on MATLAB locally; not runnable in CI |
| Simulink | Existing `.slx` closed-loop PI plant and synthetic fault/nominal variants | Executed by project author; anti-windup **builder script provided but NOT Simulink-validated** |

The **Python/C++ SIL** is genuinely coupled at each time step. The Simulink `.slx` currently runs separately; it does **not** execute C++ live. Never confuse these capabilities.

## Quick start — Windows PowerShell

Requirements: Python 3.10+, CMake, Visual Studio Build Tools C++ (or GCC/Clang). In an x64 Developer PowerShell:

```powershell
cd "C:\Users\limaj\Documents\Github\ev-hev-powertrain-safety-platform"
$env:Path += ";C:\Program Files\CMake\bin" # only if cmake command is not found
cmake -S . -B build -G "NMake Makefiles"
cmake --build build
python -m unittest discover -s tests -v
python python/closed_loop_sil.py --vehicle both --fault none
python python/closed_loop_sil.py --vehicle both --fault overtemp
python python/create_sil_report.py results/closed_loop/bev_none.csv results/closed_loop/hev_none.csv results/closed_loop/bev_overtemp.csv --output results/closed_loop/report.html
start results/closed_loop/report.html
```

If you use a Visual Studio multi-config CMake generator instead, the executable may be `build/Release/safety_supervisor.exe`; it is discovered automatically. If the compiler is not available in ordinary PowerShell, use *x64 Native Tools Command Prompt for VS* or load `vcvars64.bat` before running CMake.

For Linux/WSL:

```bash
cmake -S . -B build && cmake --build build
python3 -m unittest discover -s tests -v
python3 python/closed_loop_sil.py --vehicle both --fault none
python3 python/closed_loop_sil.py --vehicle BEV --fault can_timeout
python3 python/create_sil_report.py results/closed_loop/bev_none.csv results/closed_loop/hev_none.csv
```

## Repeatable test cases

```bash
python python/closed_loop_sil.py --vehicle BEV --fault none
python python/closed_loop_sil.py --vehicle BEV --fault low_soc
python python/closed_loop_sil.py --vehicle BEV --fault overtemp
python python/closed_loop_sil.py --vehicle HEV --fault overcurrent
python python/closed_loop_sil.py --vehicle HEV --fault can_timeout
python python/closed_loop_sil.py --vehicle HEV --fault can_counter
```

Faults are injected at **t = 24 s**, and latched FAULT cases remain faulted for the rest of the 50 s run. The sample interval is 0.1 s; results are numerical demonstration data, not vehicle calibration targets.

The prior **batch** C++ utility also works and is retained for MATLAB telemetry CSV:

```powershell
python python/generate_telemetry.py --fault overtemp --output data/telemetry.csv
.\build\safety_supervisor.exe data\telemetry.csv results\supervisor_output.csv
python python/validate_results.py --input results/supervisor_output.csv --report results/validation.html
```

## MATLAB and Simulink

Run MATLAB from repository root:

```matlab
run('matlab/generate_ev_telemetry.m')
open_system('ev_bev_closed_loop_nominal.slx')
```

To **try** generating a separate anti-windup variation from the existing Simulink nominal model:

```matlab
run('matlab/build_antiwindup_bev.m')
```

That builder is **provided for local validation only**. It is not evidence that a Simulink anti-windup model has been tested or approved. The original model files are preserved. Do not rerun the original `build_bev_closed_loop.m` in the same folder: it refuses to overwrite existing models.

## Repository map

- `cpp/` — C++17 supervisor and `--stream` request/response interface
- `python/closed_loop_sil.py` — actual BEV/HEV closed-loop software co-simulation
- `python/virtual_can.py` — project-specific CAN payload codecs
- `python/create_sil_report.py` — standalone HTML reporting
- `matlab/` — reference models and experimental Simulink builder
- `*.slx` — previously executed Simulink models (simple longitudinal BEV)
- `tests/` — automated C++/Python integration and regression tests
- `docs/` — design limitations, preliminary safety concept and evidence
- `.github/workflows/ci.yml` — automatic test job

## Engineering limitations and next steps

This is a **simulation-complete demonstration at simplified fidelity**, not a full vehicle powertrain digital twin. BMS is based on SOC, current and thermal approximations; genset uses fixed power and efficiency; regen is limited and has no friction-brake blending; CAN is a byte-level emulator and is not authenticated. No PMSM/FOC, electromagnetic inverter, verified real-time Simulink C++ coupling, production safety case, real battery pack or physical HIL is claimed. See [integration detail](docs/INTEGRATION.md) and [safety concept](docs/SAFETY_CONCEPT.md).

### Further validation to perform in MATLAB environment

- Re-run all `.slx` variants with specified Simulink version and toolbox dependencies.
- Tune PI and anti-windup on multiple reference profiles, not just one 25 s test.
- Integrate native C++ with Simulink through a tested S-function/MEX or a supported co-simulation interface, if direct Simulink-in-the-loop control is required.
- Replace the lumped vehicle/battery models and safety response by validated plant/controller models before making any physical performance or safety claim.

## Licensing and attribution

Demonstration files in this package are provided under the included `LICENSE` to the extent the publisher has rights to release them. Verify ownership and keep author credits where applicable. Do not commit license keys, proprietary data, personal account credentials or third-party artifacts without distribution rights.
