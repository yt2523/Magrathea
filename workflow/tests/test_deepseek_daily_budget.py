from pathlib import Path
import json,sys,unittest,uuid,datetime,concurrent.futures
repo=Path(__file__).resolve().parents[2];sys.path.insert(0,str(repo/'workflow'));import deepseek_daily_budget as b
class DailyBudgetTests(unittest.TestCase):
 def setUp(self):
  self.root=Path(__import__('os').environ.get('WORKFLOW_TEST_TMP','D:/Codex/tmp/workflow-daily-tests'))/uuid.uuid4().hex;self.root.mkdir(parents=True);self.ledger=self.root/'daily.json';self.seed()
 def seed(self,days=None):self.ledger.write_text(json.dumps({'schema_version':1,'timezone':'Europe/London','daily_limit':100,'days':days or {},'events':[]}))
 def reserve(self,at='2026-11-13T12:00:00+00:00'):return b.reserve_call(self.ledger,now_utc=datetime.datetime.fromisoformat(at))
 def test_100th_allowed_101st_refused_without_increment(self):
  self.seed({'2026-11-13':{'used':99}});self.assertEqual(self.reserve()['used'],100)
  with self.assertRaises(b.DailyLimitExceeded):self.reserve()
  self.assertEqual(json.loads(self.ledger.read_text())['days']['2026-11-13']['used'],100)
 def test_midnight_keeps_previous_day(self):
  self.seed({'2026-11-13':{'used':100}});self.assertEqual(self.reserve('2026-11-14T00:01:00+00:00')['used'],1);self.assertEqual(json.loads(self.ledger.read_text())['days']['2026-11-13']['used'],100)
 def test_london_summer_day(self):self.assertEqual(self.reserve('2026-03-29T23:30:00+00:00')['date'],'2026-03-30')
 def test_corrupt_ledger_refused(self):
  self.ledger.write_text('bad')
  with self.assertRaises(b.BudgetStateError):self.reserve()
 def test_missing_ledger_refused(self):
  self.ledger=self.root/'missing.json'
  with self.assertRaises(b.BudgetStateError):self.reserve()
 def test_negative_bool_counts_refused(self):
  for count in [-1,True,2.5]:
   self.seed({'2026-11-13':{'used':count}})
   with self.assertRaises(b.BudgetStateError):self.reserve()
 def test_concurrent_last_slot_only_one(self):
  self.seed({'2026-11-13':{'used':99}})
  def take(_):
   try:self.reserve();return True
   except b.DailyLimitExceeded:return False
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:out=list(e.map(take,range(8)))
  self.assertEqual(sum(out),1);self.assertEqual(json.loads(self.ledger.read_text())['days']['2026-11-13']['used'],100)
class TransportGateTests(unittest.TestCase):
 setUp=DailyBudgetTests.setUp
 seed=DailyBudgetTests.seed
 reserve=DailyBudgetTests.reserve
 def runner(self,key):
  import portable,time
  r=object.__new__(portable.Runner);r.credentials={key:'SYNTHETIC_NOT_A_SECRET'};r.coder={};r.reviewer={};r.call_timeout=1;r.max_seconds=30;r._started=time.time();return r
 def test_gate_blocks_http_before_101st(self):
  import portable
  from unittest.mock import patch,MagicMock
  self.seed({'2026-11-13':{'used':100}});opener=MagicMock()
  with patch.object(portable,'reserve_call',side_effect=self.reserve),patch.object(portable.urllib.request,'build_opener',return_value=opener):
   with self.assertRaises(portable._Pause) as e:self.runner('DEEPSEEK_API_KEY')._post_api('https://example.invalid','/mock',{},'DEEPSEEK_API_KEY')
  self.assertIn('deepseek_daily_limit_reached',str(e.exception));opener.open.assert_not_called()
 def test_other_provider_does_not_count(self):
  import portable,io
  from unittest.mock import patch,MagicMock
  opener=MagicMock();opener.open.return_value=io.BytesIO(b'{"ok":true}')
  with patch.object(portable,'reserve_call') as reserve,patch.object(portable.urllib.request,'build_opener',return_value=opener):self.assertTrue(self.runner('OPENAI_API_KEY')._post_api('https://example.invalid','/mock',{},'OPENAI_API_KEY')['ok'])
  reserve.assert_not_called()
 def test_failed_dispatch_stays_counted(self):
  import portable,urllib.error
  from unittest.mock import patch,MagicMock
  opener=MagicMock();opener.open.side_effect=urllib.error.URLError('SYNTHETIC_ONLY')
  with patch.object(portable,'reserve_call',side_effect=self.reserve),patch.object(portable.urllib.request,'build_opener',return_value=opener):
   with self.assertRaises(portable._Pause):self.runner('DEEPSEEK_API_KEY')._post_api('https://example.invalid','/mock',{},'DEEPSEEK_API_KEY')
  self.assertEqual(json.loads(self.ledger.read_text())['days']['2026-11-13']['used'],1)
 def test_stale_lock_uses_monotonic_not_wallclock(self):
  from unittest.mock import patch
  lock=Path(str(self.ledger)+'.lock');lock.mkdir()
  with patch.object(b,'LOCK_TIMEOUT',0),patch.object(b.time,'time',side_effect=AssertionError('wall clock used')):
   with self.assertRaises(b.BudgetStateError):self.reserve()
  self.assertTrue(lock.exists())
class NoProjectCapTests(unittest.TestCase):
 def test_unlimited_cap_does_not_stop_at_old_24(self):
  import portable
  r=object.__new__(portable.Runner);r.max_model_calls=None;r.state={'model_calls':10000}
  self.assertFalse(r._call_budget_exhausted())
 def test_explicit_zero_still_disables(self):
  import portable
  r=object.__new__(portable.Runner);r.max_model_calls=0;r.state={'model_calls':0}
  self.assertTrue(r._call_budget_exhausted())
if __name__=='__main__':unittest.main()
