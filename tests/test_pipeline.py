import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from generate_telemetry import generate
from virtual_can import encode_bms, decode_bms


class SafetyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = ROOT / 'build' / ('safety_supervisor.exe' if sys.platform == 'win32' else 'safety_supervisor')
        if sys.platform == 'win32' and not cls.exe.is_file():
            cls.exe = ROOT / 'build' / 'Release' / 'safety_supervisor.exe'
        if not cls.exe.is_file():
            raise unittest.SkipTest('Compile with cmake first: cmake -S . -B build && cmake --build build')

    def run_case(self, fault):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            src, dst = path / 'in.csv', path / 'out.csv'
            generate(src, fault)
            subprocess.run([str(self.exe), str(src), str(dst)], check=True, capture_output=True)
            with dst.open(newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 40)
            self.assertTrue(all(float(r['allowed_torque_nm']) == 0 for r in rows if r['state'] == 'FAULT'))
            return rows

    def test_nominal(self):
        self.assertTrue(all(r['state'] == 'NORMAL' for r in self.run_case('none')))

    def test_overtemp_latched(self):
        rows = self.run_case('overtemp')
        self.assertEqual(rows[22]['reason'], 'BATTERY_OVERTEMP')
        self.assertTrue(all(r['state'] == 'FAULT' for r in rows[22:]))

    def test_can_timeout(self):
        self.assertEqual(self.run_case('can_timeout')[22]['reason'], 'CAN_TIMEOUT')

    def test_can_counter(self):
        self.assertEqual(self.run_case('can_counter')[22]['reason'], 'CAN_COUNTER')

    def test_low_soc_derating(self):
        rows = self.run_case('low_soc')
        self.assertEqual(rows[22]['state'], 'DERATED')
        self.assertEqual(float(rows[22]['allowed_torque_nm']), 60)

    def test_overcurrent(self):
        self.assertEqual(self.run_case('overcurrent')[22]['reason'], 'OVERCURRENT')

    def test_can_codec(self):
        data = decode_bms(encode_bms(72.4, 38.2, 15))
        self.assertEqual(data, {'soc_pct': 72.4, 'battery_temp_c': 38.2, 'can_counter': 15})


if __name__ == '__main__':
    unittest.main()
