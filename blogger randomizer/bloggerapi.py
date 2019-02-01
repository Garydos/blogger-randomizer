#!/usr/bin/env python3

import urllib.parse
import urllib.request
import json
import time
import os
import pathlib
import datetime
import glob
import random
import pickle
import sys
import webbrowser

BLOGGER_API_KEY = 'AIzaSyCTqB1EERpWXzUVfU6clQW30nny7oueyEI'
BLOGGER_URL = 'https://www.googleapis.com/blogger/v3'
BLOGGER_GET_BY_URL = '/blogs/byurl?'
BLOGGER_POSTS_LIST_API = '/blogs/blogId/posts?'


def getResponse(url: str) -> str:
    '''Gets and returns the http response
    when connected to specified url'''
    
    response_obj = None
    try:
        response_obj = urllib.request.urlopen(url)
        return response_obj.read().decode(encoding = 'utf-8')
    finally:
        if response_obj != None:
            response_obj.close()

def getJSONResponse(url: str) -> 'json dict':
    '''connects to and gets a response (assumed to be in JSON) 
    from the specified url and returns the response formatted
    into a JSON object'''

    return json.loads(getResponse(url))


def buildAPIUrl(apiString: str, params: [('key','value')]) -> str:
    '''Creates the full MapQuest api url with specified params.
    API (Directions or Elevations) is specified by apiString'''
    
    queryParams = [('key', BLOGGER_API_KEY)]
    queryParams.extend(params)
    return BLOGGER_URL + apiString \
            + urllib.parse.urlencode(queryParams)

def buildPostsListAPIString(blogId: str) -> str:
    return BLOGGER_POSTS_LIST_API.replace("blogId", blogId)

def buildPostsListURL(blogId: str, params: [('key', 'value')]) -> str:
    return buildAPIUrl(buildPostsListAPIString(blogId), params)

def buildGetByUrlUrl(url: str) -> str:
    return buildAPIUrl(BLOGGER_GET_BY_URL, [('url',url)])

def getJSONPostsList(blogId: str or int, **keyvals) -> 'json dict':
    '''Uses the google blogger api to get a JSON response
    for a given blogId'''
    
    if type(blogId) is int:
        blogId = str(blogId)

    params = []
    for param in keyvals.items():
        params.append(param) 
    
    return getJSONResponse(buildPostsListURL(blogId, params))

def getJSONByUrl(url: str) -> 'json dict':
    '''Uses the google blogger api to get a JSON response
    for the given url'''

    return getJSONResponse(buildGetByUrlUrl(url))

def getIdFromJSON(resp : 'json dict') -> str:
    return resp['id']

def getBlogIdByUrl(url: str) -> str:
    return getIdFromJSON(getJSONByUrl(url)) 

def getBlogIdAndJSONPostsListByUrl(url: str, **keyvals) -> ('json dict', int):
    blogId = getBlogIdByUrl(url)
    return (getJSONPostsList(blogId, **keyvals), blogId)
        
class BloggerSite:
    def __init__(self, url: str):
        print(url)
        self._url = url
        self._url_netloc = urllib.parse.urlparse(url).netloc
        self._dir = pathlib.Path(self._url_netloc)
        self._pcleFile = pathlib.Path(self._url_netloc + '.pcle')
        self._blogId = getBlogIdByUrl(url)
        self._standardParams = {"fetchBodies":"false", "maxResults":"20"}
        self._updateFile = pathlib.Path(self._url_netloc +  ".lastupdate")
        self._jsonList = [] 
        self._postdict = dict()

    def getBlogUrl(self):
        return self._url

    def _getCurrentTime(self):
        return self._datetimeToString(datetime.datetime.utcnow())

    def _datetimeToString(self, dt):
        return dt.isoformat("T", timespec='seconds') + "Z"

    def _dateStringToDatetime(self, d: str):
        return datetime.datetime.strptime(d,'%Y-%m-%dT%H:%M:%SZ')

    def _getLastUpdateTime(self):
        time = ''
        with open(self._updateFile, 'r') as updateFile:
            time = updateFile.read() 
        if time.endswith('\n'):
            time = time[:-1]
        return time
        
    def _writeUpdateTime(self, dt):
        with open(self._updateFile,'w') as updateFile:
            updateFile.write(dt)

    def _updateTimeFile(self):
        self._writeUpdateTime(self._getCurrentTime())

    def checkForUpdates(self):
        last_update = self._getLastUpdateTime()
        currentresp, blogId = getBlogIdAndJSONPostsListByUrl(self._url, startDate=last_update, **self._standardParams)
        self._getAndStoreAllPages(currentresp, blogId, startDate=last_update)

        self._saveDatabase()
        self._updateTimeFile()

    def _addToDict(self,json_data: 'json dict'):
        for item in json_data['items']:
            self._postdict[item['id']] = (item['title'],item['url'])


    def _buildJSONFromFile(self) -> ['json dict']:
        json_dict_list = []
        for f in sorted(self._dir.glob("*.txt")):
            with open(f, 'r') as readfile:
                temp = json.load(readfile)
                json_dict_list.append(temp)
                self._addToDict(temp)
        return json_dict_list

    def _writeJSONToFile(self, resp: 'json dict', id: int): 
        if not self._dir.exists():
            os.makedirs(self._dir)
        json_file = self._dir / (str(id) + '.txt')
        with open(json_file, 'w') as outfile:
            json.dump(resp, outfile)

    def _getAndStoreAllPages(self, currentresp, blogId, **kwargs):
        while True:
            if not 'items' in currentresp:
                break;
            print('.',sep='',end='')
            sys.stdout.flush()
            self._addToDict(currentresp)
            if not 'nextPageToken' in currentresp:
                break
            currentresp = getJSONPostsList(blogId, pageToken=currentresp['nextPageToken'], **self._standardParams, **kwargs)

    def findAllPosts(self, checkForUpdates=True, refresh=False):
        if not refresh and self._pcleFile.exists():
            if (len(self._postdict) < 1):
                self._loadDatabase()
            if not checkForUpdates:
                return
            print("Checking for updates...",sep='',end='')
            sys.stdout.flush()
            self.checkForUpdates()
            print()
            return

        print("Building database...",sep='',end='')
        sys.stdout.flush()
        currentresp, blogId = getBlogIdAndJSONPostsListByUrl(self._url, **self._standardParams)
        self._getAndStoreAllPages(currentresp, blogId)
        print()
        self._saveDatabase()
        self._updateTimeFile()

    def getRandomPost(self):
        if len(self._postdict) < 1:
            return None
        return random.choice(list(self._postdict.values()))

    def getRandomPosts(self, amount):
        ret = []
        for i in range(0,amount):
            ret.append(self.getRandomPost())
        return ret


    def printRandomPosts(self, amount):
        ret = self.getRandomPosts(amount)
        for title, url in ret:
            print(title)
            print(url)
        return ret

    def openPostsInBrowser(self, posts):
        for title, url in posts:
            webbrowser.open_new_tab(url)

    def printRandomPostsAndLaunchInBrowser(self, amount):
        self.openPostsInBrowser(self.printRandomPosts(amount))

    def _loadDatabase(self):
        with open(self._pcleFile, 'rb') as handle:
            self._postdict = pickle.load(handle)

    def _saveDatabase(self):
        with open(self._pcleFile, 'wb') as handle:
            pickle.dump(self._postdict, handle, protocol=pickle.HIGHEST_PROTOCOL)

def generateBloggers(blog_file):
    return [BloggerSite(line.rstrip('\n')) for line in open(blog_file,'r')] 

def printRandomTen(blogs):
    for blog in blogs:
        print('------------')
        blog.printRandomPosts(10)
    exit(0)
            

if __name__ == '__main__':
    blogs = generateBloggers(pathlib.Path('blogs.txt'))
    checkForUpdates = True
    n = 10
    ten = False

    for arg in sys.argv:
        if arg == '-u':
            checkForUpdates = True
        if arg == '-noupdate':
            checkForUpdates = False
        if '-n' in arg:
            n = int(arg.replace('-n',''))
        if arg == '-10':
            ten = True

    for blog in blogs:
        blog.findAllPosts(checkForUpdates)

    if ten:
        printRandomTen(blogs)

    for i in range(0,n):
        blog = random.choice(blogs)
        blog.printRandomPostsAndLaunchInBrowser(1)
