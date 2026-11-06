"""Generate synthetic EV telemetry and fault-injection samples."""
import argparse
import csv
from pathlib import Path
from virtual_can import decode_bms, encode_bms, encode_torque

HEADER = ['timestamp_s', 'speed_kph', 'soc_pct', 'battery_temp_c',
          'battery_current_a', 'requested_torque_nm', 'can_age_ms', 'can_counter']


def generate(path: Path, fault: str = 'none') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(40):
        t = i * 0.1
        speed = min(50.0, i * 1.7)
        soc = 68.0 - i * 0.04
        temp = 30.0 + i * 0.15
        current = 90.0
        requested_torque = 115.0
        age_ms = 20.0
        counter = i % 16
        if i >= 22:
            if fault == 'overtemp':
                temp = 62.0
            elif fault == 'can_timeout':
                age_ms = 150.0
            elif fault == 'can_counter':
                counter = (i - 1) % 16 if i == 22 else (i - 1) % 16
            elif fault == 'low_soc':
                soc = 10.0
            elif fault == 'overcurrent':
                current = 320.0
        # Exercise the actual codec for synthetic BMS CAN frame 0x180.
        decoded = decode_bms(encode_bms(soc, temp, counter))
        _torque_payload = encode_torque(requested_torque)  # CAN ID 0x200
        rows.append([f'{t:.1f}', f'{speed:.1f}', f'{decoded["soc_pct"]:.1f}',
                     f'{decoded["battery_temp_c"]:.1f}', f'{current:.1f}',
                     f'{requested_torque:.1f}', f'{age_ms:.1f}', str(decoded['can_counter'])])
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
    print(f'Wrote {len(rows)} synthetic telemetry records to {path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/telemetry.csv')
    parser.add_argument('--fault', default='none', choices=['none', 'overtemp',
                        'can_timeout', 'can_counter', 'low_soc', 'overcurrent'])
    args = parser.parse_args()
    generate(Path(args.output), args.fault)
