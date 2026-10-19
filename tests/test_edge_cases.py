import os, tempfile, unittest
from unittest.mock import patch
_tmp=tempfile.TemporaryDirectory(prefix="musclemind-tests-")
os.environ["DATABASE_PATH"]=os.path.join(_tmp.name,"test.db")
os.environ.setdefault("SECRET_KEY","test-secret-only")
import app as m
from database import connect_db, create_tables
class EdgeCases(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  create_tables(); c=connect_db()
  try: c.execute("INSERT OR IGNORE INTO users (id,username,email,password_hash) VALUES (1,'Test','test@example.com','unused')"); c.commit()
  finally: c.close()
 def setUp(self):
  m.app.config.update(TESTING=True,SECRET_KEY="test-secret-only"); self.c=m.app.test_client()
 def login(self):
  with self.c.session_transaction() as s: s['user_id']=1; s['username']='Test'
 def test_health(self): self.assertEqual(self.c.get('/health').status_code,200)
 def test_chat_requires_login(self): self.assertEqual(self.c.post('/fitness_chat',json={'message':'hi'}).status_code,401)
 def test_empty_chat(self):
  self.login(); self.assertEqual(self.c.post('/fitness_chat',json={'message':' '}).status_code,400)
 def test_long_chat(self):
  self.login(); self.assertEqual(self.c.post('/fitness_chat',json={'message':'x'*4001}).status_code,400)
 def test_invalid_workout_weight(self):
  self.login(); r=self.c.post('/generate_workout',json={'weight':-1,'height':6.1,'goal':'gain','experience':'beginner','days':4}); self.assertEqual(r.status_code,400)
 def test_invalid_diet_meals(self):
  self.login(); r=self.c.post('/generate_diet',json={'goal':'gain','food':'veg','budget':'low','meals':99}); self.assertEqual(r.status_code,400)
 def test_infinite_progress(self):
  self.login(); self.assertEqual(self.c.post('/save_progress',json={'weight':'inf'}).status_code,400)
 def test_ai_error_is_sanitized(self):
  self.login()
  with patch.object(m,'ai_completion',side_effect=RuntimeError('private traceback')): r=self.c.post('/fitness_chat',json={'message':'hi'})
  self.assertEqual(r.status_code,503); self.assertNotIn(b'private traceback',r.data)
 def test_ai_success(self):
  self.login()
  with patch.object(m,'ai_completion',return_value='Hello'): r=self.c.post('/fitness_chat',json={'message':'hi'})
  self.assertEqual(r.status_code,200); self.assertEqual(r.get_json()['response'],'Hello')
if __name__=='__main__': unittest.main()
