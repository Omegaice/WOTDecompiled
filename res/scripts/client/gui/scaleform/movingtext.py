# Embedded file name: scripts/client/gui/Scaleform/MovingText.py
import BigWorld, time, constants
from debug_utils import *
from windows import UIInterface
from gui import GUI_SETTINGS
from gui.BattleContext import g_battleContext

class MovingText(UIInterface):
    """
    Client moving text overall.
    """
    UPDATE_INTERVAL = 600
    RSS_URL = 'http://wot.kongzhong.com/erji/ticker.xml'

    def __init__(self):
        """ Ctor. """
        UIInterface.__init__(self)
        self.__lastUpdateTime = -1

    def populateUI(self, proxy):
        UIInterface.populateUI(self, proxy)
        self.uiHolder.addExternalCallbacks({'movingText.setDisplayObject': self.onSetDisplayObject})
        self.flashDO = None
        self.__updateCbID = None
        self.__updateCallback()
        return

    def dispossessUI(self):
        if self.uiHolder is not None:
            self.uiHolder.removeExternalCallbacks('movingText.setDisplayObject')
        self.__clearCallback()
        if self.flashDO is not None:
            self.flashDO.script = None
            self.flashDO = None
        UIInterface.dispossessUI(self)
        return

    def onSetDisplayObject(self, cid, moviePath):
        """
        Setting to this python class corresponded flash component.
        Called from flash by external interface.
        
        @param cid: callback id
        @param moviePath: path of the display object in flash
        """
        try:
            self.flashDO = self.uiHolder.getMember(moviePath)
            self.flashDO.script = self
            self.uiHolder.respond([cid, True, g_battleContext.isInBattle])
        except Exception:
            LOG_ERROR('There is error while getting moving text display object')
            LOG_CURRENT_EXCEPTION()
            self.uiHolder.respond([cid, False, g_battleContext.isInBattle])

    def __clearCallback(self):
        """ Clear news updating callback """
        if self.__updateCbID is not None:
            BigWorld.cancelCallback(self.__updateCbID)
            self.__updateCbID = None
        return

    def __updateCallback(self):
        """ New updating interval handler """
        self.__update()
        self.__clearCallback()
        self.__updateCbID = BigWorld.callback(self.UPDATE_INTERVAL, self.__updateCallback)

    def __update(self):
        if not GUI_SETTINGS.movingText.show:
            return
        else:
            self.__lastUpdateTime = time.time()
            LOG_DEBUG('Requesting RSS news')
            downloadUrl = None
            if constants.IS_CHINA:
                downloadUrl = MovingText.RSS_URL
            from helpers.RSSDownloader import g_downloader
            if g_downloader is not None:
                g_downloader.download(self.__rssDownloadReceived, url=downloadUrl)
            return

    def __rssDownloadReceived(self, *args):
        """ Rss data received handler """
        if self.flashDO is not None:
            try:
                self.flashDO.updateEntries(self.__getEntries())
            except Exception:
                LOG_ERROR('There is error while updating moving text entries')
                LOG_CURRENT_EXCEPTION()

        return

    @property
    def __lastRSS(self):
        """
        @return: <dict> last requested rss data dict
        """
        from helpers.RSSDownloader import g_downloader
        if g_downloader is not None:
            return g_downloader.lastRSS
        else:
            return dict()

    def isShowMovingText(self):
        """
        Called from flash.
        
        @return: <bool> value from gui_settings.xml to show
                moving text or not
        """
        return GUI_SETTINGS.movingText.show

    def getEntries(self):
        """
        Called from flash.
        
        @return: <list of dict< 'id':<str>, 'title':<str>, 'summary':<str> >
                list of rss entries data
        """
        return self.__getEntries()

    def __getEntries(self):
        """
        @return: <list of dict< 'id':<str>, 'title':<str>, 'summary':<str> >
                list of rss entries data
        """
        result = list()
        for entry in self.__lastRSS.get('entries', list()):
            result.append({'id': entry.get('id'),
             'title': entry.get('title'),
             'summary': entry.get('summary')})

        return result

    def __findEntry(self, entryID):
        """
        Returns rss entry.
        
        @param entryID: <str> rss id to find
        @return: <dict> entry data
        """
        for entry in self.__lastRSS.get('entries', list()):
            if entry.get('id') == entryID:
                return entry

        return None

    def showBrowser(self, entryID):
        """
        Showing browser with given @entryID.
        @param entryID: <str> rss entry id
        """
        entry = self.__findEntry(entryID)
        if entry is not None:
            link = entry.get('link', '')
            openBrowser = BigWorld.wg_openWebBrowser
            if GUI_SETTINGS.movingText.internalBrowser:
                browser = getattr(self.uiHolder, 'browser')
                if browser is not None:
                    openBrowser = browser.openBrowser
                else:
                    LOG_ERROR('Attempting to open internal browser with page: `%s`, but\t\t\t\t\t\tbrowser is not exist. External browser will be opened.' % str(link))
            if len(link):
                LOG_DEBUG('Open browser at page: ', link)
                openBrowser(link)
            del openBrowser
        return