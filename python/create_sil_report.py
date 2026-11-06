"""Dependency-free standalone HTML report for BEV/HEV SIL runs."""
import argparse
import csv
import html
from collections import Counter
from pathlib import Path


def svg_line(rows,field,label,color):
    values=[float(x[field]) for x in rows]; t=[float(x['timestamp_s']) for x in rows]
    lo=min(values);hi=max(values);span=max(hi-lo,1e-8)
    width,height=960,190
    coords=' '.join(f'{30+(x-t[0])/(t[-1]-t[0] or 1)*900:.1f},{height-22-(y-lo)/span*(height-50):.1f}' for x,y in zip(t,values))
    return f'<h3>{html.escape(label)} — [{lo:.2f}, {hi:.2f}]</h3><svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(label)}" style="width:100%;border:1px solid #d0d6df;border-radius:7px"><line x1="30" y1="{height-22}" x2="930" y2="{height-22}" stroke="#9ba8b7"/><polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/></svg>'


def report(paths,output):
    chunks=[]
    for path in paths:
        with path.open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
        if not rows:raise ValueError(f'Empty CSV {path}')
        state=Counter(x['state'] for x in rows)
        chunks.append(f'<section><h2>{html.escape(path.name)}</h2><p>{len(rows)} synthetic samples · states: {html.escape(str(dict(state)))} · final SOC: {float(rows[-1]["soc_pct"]):.3f}% · fuel: {float(rows[-1]["fuel_used_l"]):.4f} L</p>')
        for f,label,color in [('speed_kph','Vehicle speed (km/h)','#2457a6'),('allowed_torque_nm','Applied torque (Nm)','#0b8f7b'),('soc_pct','Battery SOC (%)','#b76b13'),('battery_current_a','Battery current (A)','#8952ac')]:chunks.append(svg_line(rows,f,label,color))
        chunks.append('</section>')
    body='<html lang="en"><meta charset="utf-8"><title>EV/HEV SIL Report</title><style>body{font:16px system-ui;color:#1e293b;background:#f7f9fc;max-width:1080px;margin:30px auto;padding:0 20px}section{background:white;padding:24px;margin:20px 0;border-radius:12px;box-shadow:0 2px 12px #0001}h3{font-size:16px;margin:20px 0 6px}small{color:#64748b}</style><h1>EV/HEV Closed-Loop SIL</h1><p><strong>Simulation only.</strong> Illustrative powertrain and safety ECU; no ISO certification, hardware CAN, or real-time HIL.</p>'+''.join(chunks)+'</html>'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(body,encoding='utf-8');print('Report:',output)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('csv',nargs='+');p.add_argument('--output',default='results/closed_loop/report.html');a=p.parse_args();report([Path(x) for x in a.csv],Path(a.output))
