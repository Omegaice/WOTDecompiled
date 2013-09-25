import ResMgr
from debug_utils import LOG_ERROR, LOG_CURRENT_EXCEPTION, LOG_DEBUG
from helpers import i18n, getClientLanguage
import functools, Event
import Account

def __makeAchievementFileRequest(urlName, params, achievementId, callback):
    fileServerSettings = Account.g_accountRepository.fileServerSettings
    url = ''
    try:
        url = fileServerSettings[urlName]['url_template']
        url = url % params
    except KeyError:
        LOG_ERROR('Failed to find fileServer setting: %s' % urlName)
        callback(achievementId, None)
        return
    except TypeError:
        LOG_ERROR('Incorrect url format: %s' % url)
        callback(achievementId, None)
        return
    except:
        LOG_CURRENT_EXCEPTION()
        callback(achievementId, None)
        return

    fileCache = Account.g_accountRepository.customFilesCache
    fileCache.get(url, functools.partial(__fileLoadedCallback, achievementId=achievementId, dataCallback=callback), True)
    return


def __fileLoadedCallback(url, data, achievementId, dataCallback):
    dataCallback(achievementId, data)


def __getAchievementDescription(dataSection):
    result = {}
    for key, value in dataSection.items():
        result[key] = value.asString

    return result


def __allMedalsTextLoadedCallback(achievementId, data, onTextLoadedCallback):
    description = {}
    achievementIdStr = str(achievementId)
    if data is not None:
        try:
            dataSection = ResMgr.DataSection()
            dataSection.createSectionFromString(data)
            achievementsSection = dataSection['root/medals']
            for item in achievementsSection.values():
                if item.readString('id') == achievementIdStr:
                    description = __getAchievementDescription(item)
                    break

        except:
            LOG_CURRENT_EXCEPTION()
            description = {}

    onTextLoadedCallback(achievementId, description)
    return


def getRareAchievementImage(achievementId, onImageLoadedCallback):
    __makeAchievementFileRequest('rare_achievements_images', (achievementId,), achievementId, onImageLoadedCallback)


def getRareAchievementText(lang, achievementId, onTextLoadedCallback):
    cbk = functools.partial(__allMedalsTextLoadedCallback, onTextLoadedCallback=onTextLoadedCallback)
    __makeAchievementFileRequest('rare_achievements_texts', (lang,), achievementId, cbk)
