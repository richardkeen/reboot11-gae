from google.appengine.ext import db

class Session(db.Model):
  title = db.StringProperty(required=True)
  who = db.StringProperty()
  synopsis = db.StringProperty()
  start_time = db.DateTimeProperty(required=True)
  end_time = db.DateTimeProperty(required=True)
  room = db.StringProperty()
  session_type = db.StringProperty()
  description = db.TextProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  last_modified = db.DateTimeProperty()