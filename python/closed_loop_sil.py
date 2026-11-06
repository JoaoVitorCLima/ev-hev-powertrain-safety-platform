"""Synthetic BEV and series-HEV closed-loop SIL with a persistent C++ safety ECU.
No real vehicle, hardware CAN or safety certification is implied. Standard library only.
"""
import argparse
import csv
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from virtual_can import encode_bms,decode_bms,encode_torque,decode_torque

ROOT = Path(__file__).resolve().parents[1]
COLS = ['timestamp_s','vehicle_type','target_speed_kph','speed_kph','requested_torque_nm',
        'allowed_torque_nm','soc_pct','battery_temp_c','battery_current_a',
        'generator_power_kw','fuel_used_l','state','reason','can_age_ms','can_counter']


def exe_path():
    name = 'safety_supervisor.exe' if sys.platform == 'win32' else 'safety_supervisor'
    for path in (ROOT/'build'/name, ROOT/'build'/'Release'/name, ROOT/'build-msvc'/name, ROOT/'build-msvc'/'Release'/name):
        if path.exists(): return path
    raise FileNotFoundError('Compile the supervisor first using CMake; executable not found under build/')


def cycle(t):
    # Velocity profile is an illustrative maneuver, not a standardized drive cycle.
    if t < 2: return 0.0
    if t < 15: return 54.0
    if t < 22: return 34.0
    if t < 32: return 70.0
    if t < 40: return 25.0
    return 45.0


def simulate(kind='BEV', fault='none', duration=50.0, dt=0.1, exe=None):
    if kind not in ('BEV','HEV'): raise ValueError('kind must be BEV or HEV')
    if fault not in ('none','overtemp','overcurrent','low_soc','can_timeout','can_counter'):
        raise ValueError('unknown fault')
    if duration <= 0 or dt <= 0: raise ValueError('invalid time parameters')
    binary = exe or exe_path()
    proc = subprocess.Popen([str(binary), '--stream'], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            bufsize=1)
    rows=[]
    try:
        head=proc.stdout.readline().strip()
        if head != 'timestamp_s,state,allowed_torque_nm,reason':
            raise RuntimeError('Unexpected ECU response header: '+head)
        mass=1550.0 if kind=='BEV' else 1690.0
        r=0.31; ratio=9.0; drive_eff=0.91
        e_capacity_kwh=54.0 if kind=='BEV' else 9.0
        soc=68.0 if kind=='BEV' else 52.0
        speed=0.0; temp=29.0; current=0.0; integral=0.0; last_applied=0.0
        fuel_l=0.0; generator_power=0.0
        fuel_kwh_per_l=8.8 # energy at generator output fuel-basis is an illustration
        tau_i=100.0 # PI integrator time-scale, back calculation normalized by torque command
        k_p=13.0; k_i=1.0; kaw=0.10
        n=int(round(duration/dt))+1
        for i in range(n):
            t=round(i*dt,6)
            ref=cycle(t)
            # Simple 1D velocity PI with anti-windup, plus bounded regen on braking commands.
            err=ref/3.6-speed
            p_term=k_p*err
            raw=p_term+integral
            request=max(-60.0,min(180.0,raw))
            # Inject faults into telemetry delivered to the ECU, not into the plant itself.
            injected = t >= 24.0
            send_temp=65.0 if injected and fault=='overtemp' else temp
            send_current=320.0 if injected and fault=='overcurrent' else current
            send_soc=9.0 if injected and fault=='low_soc' else soc
            can_age=240.0 if injected and fault=='can_timeout' else 20.0
            counter=i%16
            if injected and fault=='can_counter' and i==int(round(24.0/dt)):
                counter=(counter+3)%16
            # Virtual BMS and VCU payload round-trip before ECU input.
            bms = decode_bms(encode_bms(send_soc, send_temp, counter))
            torque_can = decode_torque(encode_torque(request))
            send_soc, send_temp, counter = bms['soc_pct'], bms['battery_temp_c'], bms['can_counter']
            request_for_ecu = torque_can
            payload=f'{t:.3f},{speed*3.6:.3f},{send_soc:.4f},{send_temp:.4f},{send_current:.4f},{request_for_ecu:.4f},{can_age:.2f},{counter}\n'
            proc.stdin.write(payload)
            proc.stdin.flush()
            response=proc.stdout.readline().strip().split(',')
            if len(response)!=4:
                raise RuntimeError(f'Invalid supervisor response at t={t}: {response}')
            _,state,limit,reason=response
            allowed=float(limit)
            # Regenerative torque only for a negative speed request and SOC headroom.
            # This is a bounded longitudinal regen approximation, not motor FOC.
            applied = max(0.0, allowed) if soc >= 95.0 else allowed
            integral += dt*(k_i*err+kaw*(applied-raw))
            integral=max(-120.0,min(120.0,integral))
            rolling=mass*9.81*0.012 if speed>0.02 else 0.0
            aerodynamic=0.5*1.225*0.67*speed**2
            wheel_force=applied*ratio*drive_eff/r
            acc=(wheel_force-rolling-aerodynamic)/mass
            speed=max(0.0,speed+dt*acc)
            motor_omega=speed*ratio/r
            shaft_kw=applied*motor_omega/1000.0
            traction_kw=shaft_kw/0.88 if shaft_kw >= 0 else shaft_kw*0.70
            battery_kw=traction_kw+0.6
            if kind=='HEV':
                # Series hybrid: fixed-efficiency generator, on/off SOC hysteresis.
                if soc<53.0: generator_power=18.0
                elif soc>56.0: generator_power=0.0
                generator_power=min(generator_power,28.0)
                battery_kw-=generator_power
                fuel_l += generator_power*dt/3600/fuel_kwh_per_l/0.31
            soc=max(0,min(100,soc-battery_kw*dt/3600/e_capacity_kwh*100))
            # Simplified effective DC bus voltage and lumped battery thermal dynamics.
            current=battery_kw*1000/360.0
            temp+=dt*(0.000004*current**2-0.008*(temp-27.0))
            last_applied=applied
            rows.append(dict(timestamp_s=f'{t:.2f}',vehicle_type=kind,
                 target_speed_kph=f'{ref:.3f}',speed_kph=f'{speed*3.6:.3f}',
                 requested_torque_nm=f'{request:.3f}',allowed_torque_nm=f'{applied:.3f}',
                 soc_pct=f'{soc:.4f}',battery_temp_c=f'{temp:.3f}',
                 battery_current_a=f'{current:.3f}',generator_power_kw=f'{generator_power:.3f}',
                 fuel_used_l=f'{fuel_l:.6f}',state=state,reason=reason,
                 can_age_ms=f'{can_age:.1f}',can_counter=str(counter)))
        proc.stdin.close()
        if proc.wait(timeout=10)!=0:
            raise RuntimeError('ECU exited unsuccessfully: '+proc.stderr.read())
    finally:
        if proc.poll() is None: proc.kill()
        for f in (proc.stdout,proc.stderr): f.close()
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vehicle',choices=['BEV','HEV','both'],default='both')
    p.add_argument('--fault',choices=['none','overtemp','overcurrent','low_soc','can_timeout','can_counter'],default='none')
    p.add_argument('--output',default='results/closed_loop')
    a=p.parse_args()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    for kind in (['BEV','HEV'] if a.vehicle=='both' else [a.vehicle]):
        rows=simulate(kind,a.fault)
        target=out/f'{kind.lower()}_{a.fault}.csv'
        with target.open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=COLS);writer.writeheader();writer.writerows(rows)
        counts=dict(Counter(r['state'] for r in rows))
        print(f'{kind} {a.fault}: {len(rows)} SIL steps, states={counts}, SOC_end={rows[-1]["soc_pct"]}, output={target}')

if __name__=='__main__': main()
