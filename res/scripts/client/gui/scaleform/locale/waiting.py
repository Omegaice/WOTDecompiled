

class WAITING(object):
    FLASH = '#waiting:Flash'
    LOADPAGE = '#waiting:loadPage'
    LOGIN = '#waiting:login'
    ENTER = '#waiting:enter'
    LOADHANGARSPACE = '#waiting:loadHangarSpace'
    LOADHANGARSPACEVEHICLE = '#waiting:loadHangarSpaceVehicle'
    UPDATEVEHICLE = '#waiting:updateVehicle'
    UPDATECURRENTVEHICLE = '#waiting:updateCurrentVehicle'
    UPDATEMYVEHICLES = '#waiting:updateMyVehicles'
    UPDATEAMMO = '#waiting:updateAmmo'
    UPDATETANKMEN = '#waiting:updateTankmen'
    UPDATEFITTING = '#waiting:updateFitting'
    SELLVEHICLE = '#waiting:sellVehicle'
    BUYSLOT = '#waiting:buySlot'
    BUYBERTHS = '#waiting:buyBerths'
    UPDATEINVENTORY = '#waiting:updateInventory'
    SELLITEM = '#waiting:sellItem'
    BUYITEM = '#waiting:buyItem'
    UPDATESHOP = '#waiting:updateShop'
    LOADSTATS = '#waiting:loadStats'
    TRANSFERMONEY = '#waiting:transferMoney'
    EBANKBUYGOLD = '#waiting:ebankBuyGold'
    EXCHANGEVEHICLESXP = '#waiting:exchangeVehiclesXP'
    REQUESTCAPTCHA = '#waiting:requestCaptcha'
    RELOADCAPTCHA = '#waiting:reloadCaptcha'
    VERIFYCAPTCHA = '#waiting:verifyCaptcha'
    RECRUTING = '#waiting:recruting'
    EQUIPPING = '#waiting:equipping'
    UNLOADING = '#waiting:unloading'
    UPDATING = '#waiting:updating'
    STUDYING = '#waiting:studying'
    RETRAINING = '#waiting:retraining'
    DELETING = '#waiting:deleting'
    REPLACEPASSPORT = '#waiting:replacePassport'
    CUSTOMIZATIONAPPLY = '#waiting:customizationApply'
    CUSTOMIZATIONDROP = '#waiting:customizationDrop'
    C__UPDATECAPTUREDEVICES = '#waiting:__updateCaptureDevices'
    INSTALLEQUIPMENT = '#waiting:installEquipment'
    RESEARCH = '#waiting:research'
    DRAW_RESEARCH_ITEMS = '#waiting:draw_research_items'
    TECHMAINTENANCEEQUIPMENTS = '#waiting:techMaintenanceEquipments'
    TECHMAINTENANCE = '#waiting:techMaintenance'
    VOICECHAT = '#waiting:voiceChat'
    REQUESTCAPTUREDEVICES = '#waiting:requestCaptureDevices'
    STATS = '#waiting:stats'
    IN_BATTLE = '#waiting:in_battle'
    EXIT_BATTLE = '#waiting:exit_battle'
    START_BATTLE = '#waiting:start_battle'
    TRAININGCREATE = '#waiting:trainingCreate'
    TRAININGUPDATE = '#waiting:trainingUpdate'
    TRAININGJOIN = '#waiting:trainingJoin'
    TRAININGSTART = '#waiting:trainingStart'
    TRAININGDESTROY = '#waiting:trainingDestroy'
    TRAININGLEAVE = '#waiting:trainingLeave'
    APPLYMODULE = '#waiting:applyModule'
    SINHRONIZE = '#waiting:sinhronize'
    TUTORIAL_REQUEST_BONUS = '#waiting:tutorial-request-bonus'
    TUTORIAL_REQUEST_BATTLE_COUNT = '#waiting:tutorial-request-battle-count'
    TUTORIAL_REQUEST_UNLOCKS = '#waiting:tutorial-request-unlocks'
    TUTORIAL_REQUEST_VEHICLE_SETTINGS = '#waiting:tutorial-request-vehicle-settings'
    TUTORIAL_REQUEST_ELITE_VEHICLES = '#waiting:tutorial-request-elite-vehicles'
    TUTORIAL_REQUEST_CREDITS = '#waiting:tutorial-request-credits'
    TUTORIAL_REQUEST_XP = '#waiting:tutorial-request-xp'
    TUTORIAL_REQUEST_VEHICLE_EQUIPMENTS = '#waiting:tutorial-request-vehicle-equipments'
    TUTORIAL_REQUEST_INVENTORY_ITEMS = '#waiting:tutorial-request-inventory-items'
    TUTORIAL_REQUEST_TANKMAN = '#waiting:tutorial-request-tankman'
    TUTORIAL_START_TRAINING = '#waiting:tutorial-start-training'
    TUTORIAL_CHAPTER_LOADING = '#waiting:tutorial-chapter-loading'
    TUTORIAL_UPDATE_SCENE = '#waiting:tutorial-update-scene'
    TUTORIAL_REQUEST_ITEM_PARAMS = '#waiting:tutorial-request-item-params'
    TUTORIAL_REQUEST_TANKMAN_INFO = '#waiting:tutorial-request-tankman-info'
    TUTORIAL_REQUEST_SHOP = '#waiting:tutorial-request-shop'
    TUTORIAL_REQUEST_SLOTS = '#waiting:tutorial-request-slots'
    TUTORIAL_QUEUE = '#waiting:tutorial-queue'
    WAITING_EBANK_RESPONSE = '#waiting:waiting_ebank_response'
    BUTTONS_EXITQUEUE = '#waiting:buttons/exitQueue'
    BUTTONS_CEASE = '#waiting:buttons/cease'
    BUTTONS_EXIT = '#waiting:buttons/exit'
    TITLES_QUEUE = '#waiting:titles/queue'
    TITLES_REGISTERING = '#waiting:titles/registering'
    TITLES_ANOTHER_PERIPHERY = '#waiting:titles/another_periphery'
    TITLES_CHECKOUT_ERROR = '#waiting:titles/checkout_error'
    TITLES_AUTO_LOGIN_QUERY_FAILED = '#waiting:titles/auto_login_query_failed'
    MESSAGE_QUEUE = '#waiting:message/queue'
    MESSAGE_AUTOLOGIN = '#waiting:message/autoLogin'
    MESSAGE_ANOTHER_PERIPHERY = '#waiting:message/another_periphery'
    MESSAGE_CHECKOUT_ERROR = '#waiting:message/checkout_error'
    MESSAGE_AUTO_LOGIN_QUERY_FAILED = '#waiting:message/auto_login_query_failed'
    MESSAGE_AUTO_LOGIN_ACTIVATING = '#waiting:message/auto_login_activating'
    DOWNLOAD_INVENTORY = '#waiting:download/inventory'
    DOWNLOAD_SHOP = '#waiting:download/shop'
    DOWNLOAD_DOSSIER = '#waiting:download/dossier'
    UPDATINGSKILLWINDOW = '#waiting:updatingSkillWindow'
    PREBATTLE_CREATE = '#waiting:prebattle/create'
    PREBATTLE_TEAM_READY = '#waiting:prebattle/team_ready'
    PREBATTLE_TEAM_NOT_READY = '#waiting:prebattle/team_not_ready'
    PREBATTLE_PLAYER_READY = '#waiting:prebattle/player_ready'
    PREBATTLE_PLAYER_NOT_READY = '#waiting:prebattle/player_not_ready'
    PREBATTLE_ASSIGN = '#waiting:prebattle/assign'
    PREBATTLE_JOIN = '#waiting:prebattle/join'
    PREBATTLE_SWAP = '#waiting:prebattle/swap'
    PREBATTLE_CHANGE_ARENA_VOIP = '#waiting:prebattle/change_arena_voip'
    PREBATTLE_CHANGE_SETTINGS = '#waiting:prebattle/change_settings'
    PREBATTLE_LEAVE = '#waiting:prebattle/leave'
    PREBATTLE_KICK = '#waiting:prebattle/kick'
    MESSAGE_ENUM = (MESSAGE_QUEUE,
     MESSAGE_AUTOLOGIN,
     MESSAGE_ANOTHER_PERIPHERY,
     MESSAGE_CHECKOUT_ERROR,
     MESSAGE_AUTO_LOGIN_QUERY_FAILED,
     MESSAGE_AUTO_LOGIN_ACTIVATING)
    TITLES_ENUM = (TITLES_QUEUE,
     TITLES_REGISTERING,
     TITLES_ANOTHER_PERIPHERY,
     TITLES_CHECKOUT_ERROR,
     TITLES_AUTO_LOGIN_QUERY_FAILED)

    @staticmethod
    def message(key):
        outcome = '#waiting:message/%s' % key
        if outcome not in WAITING.MESSAGE_ENUM:
            raise Exception, 'locale key "' + outcome + '" was not found'
        return outcome

    @staticmethod
    def titles(key):
        outcome = '#waiting:titles/%s' % key
        if outcome not in WAITING.TITLES_ENUM:
            raise Exception, 'locale key "' + outcome + '" was not found'
        return outcome
