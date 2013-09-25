import BigWorld, ResMgr
import constants
from debug_utils import LOG_CURRENT_EXCEPTION, LOG_ERROR
from gui import GUI_SETTINGS

def _openWebSite(url, addRef = False):
    """
    Opens web browser and redirects it to the @url page
    @param url: page to redirect
    """
    try:
        if addRef:
            ds = ResMgr.openSection('../game/ref.xml' if constants.IS_DEVELOPMENT else '../ref.xml')
            if ds is not None:
                refCode = ds.readString('refCode')
                if len(refCode):
                    url = '%scode/%d' % (url, refCode)
        BigWorld.wg_openWebBrowser(url)
    except Exception:
        LOG_ERROR('There is error whiel opening web browser at page:', url)
        LOG_CURRENT_EXCEPTION()

    return


def openRegistrationWebsite():
    _openWebSite(GUI_SETTINGS.registrationURL, True)


def openRecoveryPasswordWebsite():
    """
    Opens web browser and redirects it to the
    recovery password website
    """
    _openWebSite(GUI_SETTINGS.recoveryPswdURL, True)


def isRecoveryLinkExists():
    result = 'recoveryPswdURL' in GUI_SETTINGS and len(GUI_SETTINGS.recoveryPswdURL)
    return result


def getPaymentWebsiteURL():
    url = 'http://game.worldoftanks.ru/payment/'
    try:
        url = GUI_SETTINGS.paymentURL
    except:
        LOG_CURRENT_EXCEPTION()

    try:
        import base64
        from ConnectionManager import connectionManager
        areaID = connectionManager.areaID or 'errorArea'
        loginName = connectionManager.loginName or 'errorLogin'
        userEncoded = base64.b64encode(loginName)
        url = url % {'areaID': areaID,
         'userEncoded': userEncoded}
    except:
        LOG_CURRENT_EXCEPTION()

    return url


def openPaymentWebsite():
    try:
        url = getPaymentWebsiteURL()
        if len(url) > 0:
            BigWorld.wg_openWebBrowser(url)
        else:
            LOG_ERROR('Payment website url is empty.Check tag <paymentURL> in the "text/settings.xml".')
    except Exception:
        LOG_CURRENT_EXCEPTION()


def openFinPasswordWebsite():
    try:
        url = 'http://game.worldoftanks.ru/'
        try:
            url = GUI_SETTINGS.finPasswordURL
        except:
            LOG_CURRENT_EXCEPTION()

        BigWorld.wg_openWebBrowser(url)
    except Exception:
        LOG_CURRENT_EXCEPTION()


def openMigrationWebsite(login):
    try:
        url = 'http://game.worldoftanks.ru/migration/%s'
        try:
            url = GUI_SETTINGS.migrationURL
        except:
            LOG_CURRENT_EXCEPTION()

        BigWorld.wg_openWebBrowser(url % login)
    except Exception:
        LOG_CURRENT_EXCEPTION()


def openSecuritySettingsPage():
    url = ''
    if 'securitySettingsURL' in GUI_SETTINGS and len(GUI_SETTINGS.securitySettingsURL):
        url = GUI_SETTINGS.securitySettingsURL
    if len(url):
        BigWorld.wg_openWebBrowser(url)
