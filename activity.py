#!/usr/bin/env python
import os
import wsgiref.handlers
from future import Future
from time import time
import feedparser
import simplejson as json
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp

class ActivityHandler(webapp.RequestHandler):
  
  def render(self,template_file, context={}):
    path = os.path.join(os.path.dirname(__file__), template_file)
    self.response.out.write(template.render(path, context))
  
  def fetch_feeds(self):
    hit_list = [ "http://search.twitter.com/search.atom?q=%23reboot11", "http://www.jaiku.com/channel/reboot/atom" ]
    
    # pull down all feeds
    future_calls = [Future(feedparser.parse,rss_url) for rss_url in hit_list]
    # block until they are all in
    feeds = [future_obj() for future_obj in future_calls]
    
    entries = []
    for feed in feeds:
      entries.extend( feed[ "items" ] )
    
    entries = entries[0:20]
    
    decorated = [(entry["date_parsed"], entry) for entry in entries]
    decorated.sort()
    decorated.reverse() # for most recent entries first
    sorted = [{ "title" : entry["title"], "link" : entry["link"], "author" : entry["author_detail"]["name"], "published": entry["published"]} for (date,entry) in decorated]
    return sorted
    
  
  def get(self, type):

    # check memcached for last request time    
    last_updated = memcache.get("activity/last_updated")
    
    entries = []
    
    # if memcached is empty
    if last_updated is None:
      # get latest 30 messages
      entries = self.fetch_feeds()
      # set memcached timestamp and messages
      memcache.set("activity/last_updated", value = time())
      memcache.set("activity/stream", value = entries)
    else:
      # if timestamp is more than 30 seconds ago
      if time() - last_updated > 30:
        # get latest 30 messages
        entries = self.fetch_feeds()
        # set memcached timestamp and messages
        memcache.set("activity/last_updated", value = time())
        memcache.set("activity/stream", value = entries)
      else:
        # return memcached results
        entries = memcache.get("activity/stream")
    
    if type == '.json':
      self.response.headers['Content-Type'] = 'application/javascript'
      self.response.out.write(json.dumps(entries))
    else:
      context = { 'entries': entries }
      self.render('templates/activity.html', context)
    
  

def main():
  application = webapp.WSGIApplication([('/activity(\.json)?', ActivityHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
