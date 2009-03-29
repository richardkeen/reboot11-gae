#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import wsgiref.handlers
import models
import simplejson
import datetime
import logging
import time
import os

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template

class ScheduleHandler(webapp.RequestHandler):
  def render(self,template_file, context={}):
    path = os.path.join(os.path.dirname(__file__), template_file)
    self.response.out.write(template.render(path, context))

  def get(self, type):
    sessions = models.Session.all()
    sessions.order('start_time')
    
    schedule = {}
    
    for session in sessions:
      day = session.start_time.strftime('%Y-%m-%d')
      if day not in schedule:
        schedule[day] = {}
      
      s_time = session.start_time.strftime('%H:%M')
      if s_time not in schedule[day]:
        schedule[day][s_time] = []
        
      schedule[day][s_time].append(session)
      
    schedule_output = []

    days = schedule.keys()
    days.sort()
    for day in days:
      day_schedule = []
      times = schedule[day].keys()
      times.sort()
      for s_time in times:
        day_schedule.append( { 'start_time': s_time,
                               'sessions': schedule[day][s_time]
                             }
                           )
                           
      schedule_output.append(day_schedule)

    if type == '.json':
      json = GqlEncoder().encode(schedule_output)
      self.response.headers['Content-Type'] = 'application/javascript'
      self.response.out.write(json)
    else:
      context = { 'schedule': schedule_output }
      self.render('templates/schedule.html', context)

  def post(self, format):
    session = models.Session(
                title        = self.request.get('title'),
                who          = self.request.get('who'),
                start_time   = datetime.datetime.strptime(self.request.get('start_time'), '%Y-%m-%d %H:%M'),
                end_time     = datetime.datetime.strptime(self.request.get('end_time'), '%Y-%m-%d %H:%M'),
                room         = self.request.get('room'),
                session_type = self.request.get('session_type'),
                description  = self.request.get('description'),
                synopsis     = self.request.get('synopsis')
              )
    session.put()
    self.redirect('/schedule')
    
class TempHandler(webapp.RequestHandler):

  def get(self):
    for i in range(20):
      session = models.Session( title = "small room Session %s" % i,
                                start_time = datetime.datetime.now() + datetime.timedelta(hours = i),
                                end_time = datetime.datetime.now() + datetime.timedelta(hours = i+1))      
      session.put()  

class GqlEncoder(simplejson.JSONEncoder):

  """Extends JSONEncoder to add support for GQL results and properties.

  Adds support to simplejson JSONEncoders for GQL results and properties by
  overriding JSONEncoder's default method.
  """

  # TODO Improve coverage for all of App Engine's Property types.

  def default(self, obj):

    """Tests the input object, obj, to encode as JSON."""

    if hasattr(obj, '__json__'):
      return getattr(obj, '__json__')()

    if isinstance(obj, db.GqlQuery):
      return list(obj)

    elif isinstance(obj, db.Model):
      properties = obj.properties().items()
      output = {}
      for field, value in properties:
        output[field] = getattr(obj, field)
      return output

    elif isinstance(obj, datetime.datetime):
      return obj.strftime('%Y-%m-%d %H:%M')

    elif isinstance(obj, time.struct_time):
      return list(obj)

    elif isinstance(obj, users.User):
      output = {}
      methods = ['nickname', 'email', 'auth_domain']
      for method in methods:
        output[method] = getattr(obj, method)()
      return output

    return simplejson.JSONEncoder.default(self, obj)

def main():
  application = webapp.WSGIApplication([('/schedule(\.json)?', ScheduleHandler),
                                        ('/schedule/temp', TempHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
