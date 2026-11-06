"""Validate C++ safety-supervisor CSV output and produce an HTML summary."""
import argparse
import csv
import html
from pathlib import Path


def validate(path: Path, report: Path) -> bool:
    with path.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError('Empty supervisor output')
    counts = {s: sum(r['state'] == s for r in rows) for s in ['NORMAL', 'DERATED', 'FAULT']}
    unsafe = [r for r in rows if r['state'] == 'FAULT' and float(r['allowed_torque_nm']) != 0]
    valid = not unsafe
    report.parent.mkdir(parents=True, exist_ok=True)
    tr = ''.join(f'<tr><td>{html.escape(r["timestamp_s"])}</td><td>{html.escape(r["state"])}</td>'
                 f'<td>{html.escape(r["allowed_torque_nm"])}</td><td>{html.escape(r["reason"])}</td></tr>' for r in rows)
    report.write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>EV/HEV SIL Validation</title>'
                      '<style>body{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 16px}'
                      'table{border-collapse:collapse;width:100%}td,th{padding:8px;border-bottom:1px solid #ddd}'
                      'th{text-align:left}h1{color:#17365d}</style><h1>EV / HEV — Simulation-in-the-Loop Safety Check</h1>'
                      '<p><strong>SYNTHETIC DATA. NOT VEHICLE-CERTIFIED SAFETY VALIDATION.</strong></p>'
                      f'<p>Records: {len(rows)} | NORMAL: {counts["NORMAL"]} | DERATED: {counts["DERATED"]}'
                      f' | FAULT: {counts["FAULT"]} | Check: {"PASS" if valid else "FAIL"}</p>'
                      '<table><thead><tr><th>t (s)</th><th>State</th><th>Allowed torque (Nm)</th>'
                      '<th>Reason</th></tr></thead><tbody>' + tr + '</tbody></table></html>', encoding='utf-8')
    print(f'{"PASS" if valid else "FAIL"}: {len(rows)} frames; {counts}; report={report}')
    return valid


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='results/supervisor_output.csv')
    parser.add_argument('--report', default='results/validation.html')
    args = parser.parse_args()
    raise SystemExit(0 if validate(Path(args.input), Path(args.report)) else 1)
