import sys, unittest, sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import fixture,check,xy
from collections import Counter
class QualityTests(unittest.TestCase):
 def test_expected_findings(self):
  findings=check(*fixture())
  self.assertEqual(Counter(x['code'] for x in findings),{'DUPLICATE_ID':2,'MISSING_DIAMETER':1,'INVALID_DIAMETER':1,'ZERO_LENGTH':1,'DUPLICATE_GEOMETRY':1,'NEAR_GAP':1,'DISCONNECTED':3,'OFF_NETWORK_VALVE':1})
 def test_exact_affected_rows(self):
  f=check(*fixture())
  self.assertEqual({(x['code'],x['row_id']) for x in f},{('DUPLICATE_ID',1),('DUPLICATE_ID',2),('MISSING_DIAMETER',3),('INVALID_DIAMETER',4),('ZERO_LENGTH',29),('DUPLICATE_GEOMETRY',30),('NEAR_GAP',32),('DISCONNECTED',32),('DISCONNECTED',33),('DISCONNECTED',34),('OFF_NETWORK_VALVE',2)})
 def test_clean_terminal_and_valve(self):
  p=[dict(row_id=1,asset_id='OK',diameter_mm=100,terminal_end=True,coords=[xy(0,0),xy(100,0)])]
  v=[dict(row_id=1,asset_id='V',coords=xy(50,0))]; s=[dict(row_id=1,asset_id='S',coords=xy(0,0))]
  self.assertEqual(check(p,v,s),[])
 def test_crossing_does_not_connect(self):
  p,v,s=fixture(); f=check(p,v,s)
  self.assertIn(34,[x['row_id'] for x in f if x['code']=='DISCONNECTED'])
 def test_gap_threshold(self):
  p=[dict(row_id=1,asset_id='A',diameter_mm=100,coords=[xy(0,0),xy(100,0)]),dict(row_id=2,asset_id='B',diameter_mm=100,coords=[xy(102,0),xy(200,0)])]
  s=[dict(row_id=1,asset_id='S',coords=xy(0,0))]
  self.assertEqual(sum(x['code']=='NEAR_GAP' for x in check(p,[],s)),1)
  p[1]['coords'][0]=xy(102.01,0)
  self.assertEqual(sum(x['code']=='NEAR_GAP' for x in check(p,[],s)),0)
 def test_repair_preserves_geometry(self):
  p,v,s=fixture(); import copy
  clean=copy.deepcopy(p); clean[0]['asset_id']='H00';clean[1]['asset_id']='H10'
  self.assertEqual([x['coords'] for x in clean],[x['coords'] for x in p])
  self.assertEqual(len(check(clean,v,s)),9)
 def test_geopackage(self):
  path=Path(__file__).resolve().parents[1]/'data/network.gpkg'
  with sqlite3.connect(path) as con:
   self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0],'ok')
   for layer,n in [('pipes_raw',34),('pipes_clean',34),('valves',2),('sources',1),('qa_before',11),('qa_after',9)]:
    self.assertEqual(con.execute(f'SELECT count(*) FROM {layer}').fetchone()[0],n)
   self.assertEqual({r[0] for r in con.execute('SELECT srs_id FROM gpkg_geometry_columns')},{32638})
if __name__=='__main__': unittest.main()
