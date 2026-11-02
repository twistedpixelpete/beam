import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('beam_faults',Path(__file__).resolve().parents[1]/'projection_study'/'faults.py')
faults=importlib.util.module_from_spec(spec); spec.loader.exec_module(faults)


class Guarded(unittest.TestCase):
    def setUp(self):
        faults.clear()

    def test_exception_keeps_timer_alive_and_is_reported(self):
        calls=[]
        @faults.guarded('Work',retry=2.5)
        def tick():
            calls.append(1)
            raise TypeError('bad enum')
        with self.assertLogs('beam',level='ERROR') as logs:
            self.assertEqual(tick(),2.5)
            self.assertEqual(tick(),2.5)
        self.assertEqual(len(calls),2)
        self.assertEqual(len(logs.records),1,'an unchanged failure must not flood the console')
        self.assertEqual(faults.summary(),('Work: TypeError: bad enum',))

    def test_recovery_clears_fault_and_keeps_interval(self):
        state={'fail':True}
        @faults.guarded('Work')
        def tick():
            if state['fail']:raise ValueError('x')
            return 1/30
        with self.assertLogs('beam',level='ERROR'):tick()
        state['fail']=False
        self.assertEqual(tick(),1/30)
        self.assertEqual(faults.summary(),())

    def test_none_still_stops_timer(self):
        @faults.guarded('Work')
        def tick():return None
        self.assertIsNone(tick())

    def test_wraps_identity_for_timer_registration(self):
        @faults.guarded('Work')
        def tick():return 1
        self.assertEqual(tick.__name__,'tick')


if __name__=='__main__':unittest.main()
