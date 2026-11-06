import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'python'))
from closed_loop_sil import simulate, exe_path
from virtual_can import encode_torque,decode_torque,encode_bms,decode_bms

class ClosedLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:cls.exe=exe_path()
        except FileNotFoundError as e:raise unittest.SkipTest(str(e))

    def test_bev_nominal_and_regen(self):
        rows=simulate('BEV','none',exe=self.exe)
        self.assertEqual(len(rows),501)
        self.assertTrue(all(x['state']=='NORMAL' for x in rows))
        self.assertTrue(any(float(x['allowed_torque_nm']) < -10 for x in rows))
        self.assertTrue(any(float(x['battery_current_a']) < 0 for x in rows))
        self.assertGreater(float(rows[-1]['soc_pct']),0)

    def test_series_hybrid_generator_and_fuel(self):
        rows=simulate('HEV','none',exe=self.exe)
        self.assertTrue(any(float(x['generator_power_kw'])>0 for x in rows))
        self.assertGreater(float(rows[-1]['fuel_used_l']),0)
        self.assertGreaterEqual(float(rows[-1]['soc_pct']),0)

    def test_faults_latch_and_clear_torque(self):
        for fault,reason in [('overtemp','BATTERY_OVERTEMP'),('overcurrent','OVERCURRENT'),
                             ('can_timeout','CAN_TIMEOUT'),('can_counter','CAN_COUNTER')]:
            with self.subTest(fault=fault):
                rows=simulate('BEV',fault,exe=self.exe)
                self.assertEqual(rows[240]['reason'],reason)
                self.assertTrue(all(x['state']=='FAULT' and float(x['allowed_torque_nm'])==0
                                    for x in rows[240:]))

    def test_low_soc_derating(self):
        rows=simulate('HEV','low_soc',exe=self.exe)
        self.assertEqual(rows[240]['state'],'DERATED')
        self.assertTrue(all(-20<=float(x['allowed_torque_nm'])<=60 for x in rows[240:]))

    def test_can_payload_round_trip(self):
        self.assertEqual(decode_torque(encode_torque(-45.2)),-45.2)
        self.assertEqual(decode_bms(encode_bms(52.5,39.0,4))['soc_pct'],52.5)
        with self.assertRaises(ValueError):decode_torque(b'123')

if __name__=='__main__':unittest.main()
