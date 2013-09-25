# Embedded file name: scripts/client/helpers/RSSDownloader.py
import threading
import helpers
import BigWorld
import ResMgr
import feedparser
from debug_utils import *
_CLIENT_VERSION = helpers.getClientVersion()
feedparser.PARSE_MICROFORMATS = 0
feedparser.SANITIZE_HTML = 0

class RSSDownloader:
    UPDATE_INTERVAL = 0.1
    MIN_INTERVAL_BETWEEN_DOWNLOAD = 60.0
    lastRSS = property(lambda self: self.__lastRSS)
    isBusy = property(lambda self: self.__thread is not None)

    def __init__(self):
        self.url = ''
        ds = ResMgr.openSection('gui/gui_settings.xml')
        if ds is not None:
            self.url = ds.readString('rssUrl')
        self.__thread = None
        self.__lastDownloadTime = 0
        self.__cbID = BigWorld.callback(self.UPDATE_INTERVAL, self.__update)
        self.__lastRSS = {}
        self.__onCompleteCallbacks = set()
        return

    def destroy(self):
        self.__thread = None
        self.__onCompleteCallbacks = None
        if self.__cbID is not None:
            BigWorld.cancelCallback(self.__cbID)
            self.__cbID = None
        return

    def download(self, callback, url = None):
        if callback is None:
            return
        else:
            if url is None:
                url = self.url
            if self.__thread is not None:
                self.__onCompleteCallbacks.add(callback)
            else:
                time = BigWorld.time()
                if self.__lastDownloadTime != 0 and time - self.__lastDownloadTime < self.MIN_INTERVAL_BETWEEN_DOWNLOAD:
                    callback(self.__lastRSS)
                else:
                    self.__lastDownloadTime = time
                    self.__thread = _WorkerThread(url)
                    self.__onCompleteCallbacks.add(callback)
            return

    def __update(self):
        self.__cbID = BigWorld.callback(self.UPDATE_INTERVAL, self.__update)
        if self.__thread is None or self.__thread.isAlive():
            return
        else:
            if self.__thread.result is not None:
                self.__lastRSS = self.__thread.result
            for callback in self.__onCompleteCallbacks:
                try:
                    callback(self.__lastRSS)
                except:
                    LOG_CURRENT_EXCEPTION()

            self.__onCompleteCallbacks = set()
            self.__thread = None
            return


class _WorkerThread(threading.Thread):

    def __init__(self, url):
        super(_WorkerThread, self).__init__()
        self.url = url
        self.result = None
        self.name = 'RSS Downloader thread'
        self.start()
        return

    def run(self):
        try:
            self.result = feedparser.parse(self.url, None, None, _CLIENT_VERSION)
        except:
            LOG_CURRENT_EXCEPTION()

        return


g_downloader = None

def init():
    global g_downloader
    g_downloader = RSSDownloader()