# Integrated SIL workflow

1. Python generates synthetic vehicle reference and advances a longitudinal plant at 100 ms steps.
2. Synthetic CAN BMS and VCU payloads are encoded and decoded in Python with documented project-specific scaling.
3. Each step is sent over a persistent **stdin/stdout** CSV protocol to the real compiled **C++17** supervisor, which retains its CAN-counter and latched-fault state between calls.
4. C++ returns `NORMAL`, `DERATED`, or `FAULT` and a constrained torque; Python applies this torque to the **next plant integration step** and updates battery SOC/temperature and optional HEV generator energy.
5. CSV traces, regression checks and HTML plots document results.

This **is genuine closed-loop software co-simulation between Python and C++**, but it is not deterministic real-time execution, in-vehicle CAN, or a direct C++ S-function/MEX in Simulink. The existing Simulink `.slx` is an independently run comparative plant; MATLAB Engine/MEX integration remains unverified.

## Mathematical approximations

- Longitudinal force `F = Tmotor * ratio * driveline_eff / wheel_radius - Crr*m*g - 0.5*rho*CdA*v^2`.
- `v[k+1] = max(0,v[k] + dt*F/m)` using explicit Euler at `dt=0.1 s`.
- Battery power from shaft mechanical power with constant discharge/regen efficiency, plus fixed accessory load.
- Battery SOC from integrated battery power and nominal usable kWh, not an equivalent circuit.
- Series HEV generator is a simple constant-power source driven by SOC hysteresis, with estimated fuel energy (not calibrated BSFC).
- PI controller with a bounded integrator and back-calculation based on **applied C++ torque**, not PI request.

## Known limits

No PMSM electromagnetic dynamics, PWM inverter, field-oriented control, detailed battery ECM/aging, real motor torque-speed envelope, hydraulic/friction brake blending, gear backlash, tire slip, thermal coolant loop, road grade, or physical actuator timing. Sensor validity, adversarial network security and functional safety mechanisms are highly simplified. Results are demonstration data, **not performance predictions for actual BEV/HEV**.
