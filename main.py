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
import datetime
from google.appengine.api import users
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template, util

import logging
import markdown


class BaseHandler(webapp.RequestHandler):
    def render_template(self,templateFilename,templateVars,postLoginURL=None):
        if postLoginURL is None:
            postLoginURL = self.request.uri
        newVars = dict(templateVars)
        newVars['user'] = users.get_current_user()
        newVars['current_user_admin'] = users.is_current_user_admin()
        if newVars.get('user'): 
            newVars['logoutURL'] = users.create_logout_url(postLoginURL)
        else:
            newVars['loginURL'] = users.create_login_url(postLoginURL)
        self.response.out.write(template.render(templateFilename,newVars))

class BlogPost(db.Model):
    title = db.StringProperty()
    contents = db.TextProperty()
    author = db.StringProperty()
    date = db.DateTimeProperty()

class PreferredName(db.Model):
    name = db.StringProperty()
    
class NewUserID(db.Model):
    id = db.StringProperty()
    preferred = db.ReferenceProperty(PreferredName)

class SubmitHandler(BaseHandler):
    def post(self):
        if users.get_current_user() is not None:
            newPost = BlogPost()
            newPost.title = self.request.get('post-title')
            md = markdown.Markdown(safe_mode="replace")
            newPost.contents = md.convert(self.request.get('post-contents'))
            newPost.author = users.get_current_user().nickname()
            newPost.date = datetime.datetime.now()
            newPost.put()
        allBlogEntries = BlogPost.all()
        allBlogEntries.order('-date')
        allBlogObjs = allBlogEntries.fetch(1000)
        self.render_template("templates/entries.html",{ 'posts': allBlogObjs })
#        logging.info(self.request.get('tweetText'))

class MainHandler(BaseHandler):
    def get(self):
        allBlogEntries = BlogPost.all()
        authorName = self.request.get('author')
        if authorName:
            allBlogEntries.filter('author = ', authorName)
        allPosts = allBlogEntries.order('-date').fetch(1000)
        self.render_template("templates/index.html", {"posts" : allPosts})


def main():
    application = webapp.WSGIApplication([('/', MainHandler), ('/submit', SubmitHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
