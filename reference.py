#-*- coding: utf-8 -*-
import os
import sys
import subprocess
import threading
import json
import time
import math
from time import mktime
from datetime import datetime

from logVerifier22 import LogVerifier

#==============================================================================
# Global Value
UCM_LIVE_KIND = 'com.webos.service.usercontextmanager.channel:1'
UCM_STB_KIND = 'com.webos.service.usercontextmanager.stb:1'
UCM_APP_KIND = 'com.webos.service.usercontextmanager.app:1'
bAutomatic = False
currAccount = ''

localeLists = [ "af-ZA", "am-ET", "ar-SA", "as-IN", "az-Latn-AZ", "bg-BG", "bn-IN", "bs-Latn-BA", "cs-CZ", "da-DK", "de-DE", "el-GR", "en-GB", "es-CO", "es-ES", "et-EE",
                "fa-IR", "fi-FI", "fr-CA", "fr-FR", "ga-IE", "gu-IN", "ha-Latn-NG", "he-IL", "hi-IN", "hr-HR", "hu-HU", "id-ID", "it-IT", "ja-JP", "kk-Cyrl-KZ", "km-KH", "kn-IN", "ko-KR", "ku-Arab-IQ",
                "lt-LT", "lv-LV", "mk-MK", "ml-IN", "mn-Cyrl-MN", "mr-IN", "ms-MY", "nb-NO", "nl-NL", "or-IN", "pa-IN", "pl-PL", "pt-BR", "pt-PT", "ro-RO", "ru-RU",
                "si-LK", "sk-SK", "sl-SI", "sq-AL", "sr-Latn-RS", "sv-SE", "sw-Latn-KE", "ta-IN", "te-IN", "th-TH", "tr-TR", "uk-UA", "ur-IN", "uz-Latn-UZ", "vi-VN",
                "zh-Hans-CN", "zh-Hant-HK", "zh-Hant-TW", "is-IS", "en-US" ]
#localeLists = ["ko-KR"]

def convertNudgeResult(var):
    # for nudgeResult
    if var == 'TIMEOUT':
        return 0
    elif var == 'CLOSED':
        return 1
    elif var == 'SELECTED':
        return 2

    elif var == 0:
        return 'TIMEOUT'
    elif var == 1:
        return 'CLOSED'
    elif var == 2:
        return 'SELECTED'
    return "UNDEFINED";

def convertNudgeState(var):
    # for nudgeState
    if var == 'READY':
        return 0
    elif var == 'SUSPENDED':
        return 1
    elif var == 'TERMINATED':
        return 2

    elif var == 0:
        return 'READY'
    elif var == 1:
        return 'SUSPENDED'
    elif var == 2:
        return 'TERMINATED'

    return "UNDEFINED";


def runSystem(cmd):
    out = subprocess.check_output(cmd, shell=True)
    return out

def lunaCommand(api, payload, sender = 'com.webos.service.nudge' ):
    cmd = "luna-send -n 1 -a {0} -f {1} \'{2}\'".format(sender, api, json.dumps(payload) );
    return runSystem(cmd)

def convert2Timestamp( yy, mm, dd, h, m, s):
    dt2 = datetime( yy, mm, dd, h, m, s)
    return dt2.strftime("%s")

def convert2Timestamp( st ):
    dt2 = datetime( st.tm_year, st.tm_mon, st.tm_mday, st.tm_hour, st.tm_min, st.tm_sec)
    return dt2.strftime("%s")

def convert2Date( ts ):
    return datetime.fromtimestamp( float(ts) )

def convert2YYYYMMDD( day = 0 ):
    st = time.localtime()
    tm = int(convert2Timestamp(st))
    tm = tm + (day*60*60*24)

    tl = time.localtime(tm)

    ymd = '%4d%02d%02d' % ( tl.tm_year, tl.tm_mon, tl.tm_mday );
    return int(ymd)

def convert2YYYYMMDDOfBroadcast( day = 0 ):
    api = 'luna://com.palm.systemservice/time/getEffectiveBroadcastTime'
    ret = lunaCommand( api, {})
    retObj = json.loads(ret)
    bRet, adjustedUtc = jsonGetKeyValue(retObj, 'adjustedUtc')
    if bRet == False : return 0
    tm = adjustedUtc + (day*60*60*24)

    tl = time.localtime(tm)

    ymd = '%4d%02d%02d' % ( tl.tm_year, tl.tm_mon, tl.tm_mday )
    return int(ymd)

def convert2HHMMSS( hour = 0, minute = 0, second = 0 ):
    st = time.localtime()
    tm = int(convert2Timestamp(st))
    tm = tm + (hour*60*60)
    tm = tm + (minute*60)
    tm = tm + second

    tl = time.localtime(tm)

    hms = '%02d%02d%02d' % ( tl.tm_hour, tl.tm_min, tl.tm_sec );
    return int(hms)


def jsonCheckKeyValue( obj, key, value ):
    try :
        if (key in obj) and (obj[key] == value):
            return True
        return False

    except Exception as ex:
        print('Exception : ', ex)
        return False

def jsonGetKeyValue( obj, key):
    try :
        if key in obj:
            value = obj[key];
            return True, value
        return False, None

    except Exception as ex:
        print('Exception : ', ex)
        return False, None

#==============================================================================

def attachLogVerifier():
    for osCmd in preCondition:
        print("PreCondition : ", osCmd)
        os.system(osCmd)

    # target run
    testResult = []
    cmdList = targetProc
    cond = threading.Condition()
    tcQueue = Queue.Queue();
    tcQueue.__init__()

    t = threading.Thread(target=taskMainProc, args=(cmdList, cond, tcQueue ))
    t.start()

    sleep(1)
    print(" * DONE : attachLogVerifier")
    return tcQueue

#==============================================================================
def getLoginId():
    api = 'luna://com.webos.service.accountmanager/getLoginID'
    payload = {"serviceName": "LGE"}
    ret = lunaCommand( api, payload);
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False, None
    #bRet, account = jsonGetKeyValue( retObj, "id")
    bRet, account = jsonGetKeyValue( retObj, "lastSignInUserNo")
    return bRet, account

def setSettings( category, key, value) :
    api = 'luna://com.webos.service.settings/setSystemSettings'
    payload = { "category": category, "settings": { key : value } }
    return lunaCommand( api, payload )

def changeLocale(loc):
    api = "luna://com.webos.settingsservice/setSystemSettings"
    payload = {
        "settings": {
            "localeInfo": {
                "locales": {
                    "UI": loc
                }
            }
        }
    }
    ret = lunaCommand( api, payload )
    print(" - SetLocale : ",  ret)
    time.sleep(0.1)
    return

def launchDMRPopup():
    api = "luna://com.webos.service.dmrsvc/verifyUse"
    payload = {
        "serviceName": "svc",
        "methodName": "STRING-CHECK",
        "parameters": "param",
        "magicNumber": 0
    }
    ret = lunaCommand( api, payload )
    print(" - Launch DMR Popup : ", ret)
    time.sleep(0.1)
    return

def captureScreen( path ):
    api = "luna://com.webos.service.capture/executeOneShot"
    payload = {
        "path": path,
        "method": "DISPLAY",
        "width": 1920,
        "height": 1080,
        "format": "JPEG"
    }

    time.sleep(0.5)
    ret = lunaCommand( api, payload )
    print(" - Capture screen(%s) : %r" % (path, ret))
    time.sleep(0.1)
    return

def enterKey( key = "ENTER"):
    api = "luna://com.webos.service.networkinput/sendSpecialKey"
    payload = {
        "key" : key
    }

    ret = lunaCommand( api, payload )
    #print(" - Enter key(%s) : %r" % (key, ret))
    time.sleep(0.1)
    return


def getForegorundApp() :
    api = 'luna://com.palm.applicationManager/getForegroundAppInfo'
    payload = {}

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False, None

    bRet, appId = jsonGetKeyValue( retObj, "appId")
    return bRet, appId

def checkLiveTV( appId = None):
    if appId == None :
        bRet, appId = getForegorundApp()
        if bRet == False : return bRet
    if appId == 'com.webos.app.livetv':
        return True
    return False

def checkSTBApp( appId = None ):
    if appId == None :
        bRet, appId = getForegorundApp()
        if bRet == False : return bRet

    api = 'luna://com.webos.service.eim/getAllInputStatus'
    payload = {}

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret.decode('utf-8', 'ignore').encode('utf-8'))
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, jResults = jsonGetKeyValue( retObj, "devices")
    i = 0;
    for obj in jResults:
        bRet, objAppId = jsonGetKeyValue( obj, "appId")
        if bRet == False or appId != objAppId :
            continue

        bRet, objActive = jsonGetKeyValue( obj, "activate")
        if bRet == False or objAppId == False :
            continue

        bRet, objSub = jsonGetKeyValue( obj, "subList")
        if bRet == False :
            continue

        if len(objSub) > 0 :
            bRet, stype = jsonGetKeyValue( objSub[0], "serviceType" )
            if bRet == False or stype != "settop" :
                continue
        return True
    return False

def getLiveTVChannelInfo():
    api = 'luna://com.webos.service.utp.channel/getLastChannelId'
    payload = {"sourceType" : "INPUTSOURCE_NONE"}

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False
    bRet, channelId = jsonGetKeyValue(retObj, 'channelId')
    if bRet == False : return False
    #return bRet, channelId

    api = 'luna://com.webos.service.iepg/getChannelInfo'
    payload = {"dataType":0,"channelId": channelId }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, chList = jsonGetKeyValue(retObj, 'channelList' )
    if bRet == False : return False
    chObj = chList[0]

    bRet, channelIcon = jsonGetKeyValue(chObj, 'imgUrl')
    if bRet == False : return False
    bRet, channelName = jsonGetKeyValue(chObj, 'channelName')
    channelName = str(channelName.encode('utf8'))
    if bRet == False : return False
    bRet, channelNumber = jsonGetKeyValue(chObj, 'channelNumber')
    if bRet == False : return False

    return True, channelId, channelIcon, channelName, channelNumber

def getSTBChannelInfo():
    api = 'luna://com.webos.service.scd/getCurrentChannelNumber'
    payload = {}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, detectedChannelNumber = jsonGetKeyValue( retObj, "detectedChannelNumber" )
    if bRet == False :
        print('WARN] Not ready to detect settop number')
        return False
    print(detectedChannelNumber)
    channelNumber = detectedChannelNumber.lstrip('0')

    api = 'luna://com.webos.service.iepg/getChannelList'
    payload = {
        "dataType": 0,
        "channelMode": ["STB"],
        "channelGroup": ["All"],
        "attribute": [{
            "filterType": "channelNumber",
            "value": channelNumber
        }]
    }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, chList = jsonGetKeyValue( retObj, "channelList" )
    if bRet == False : return False

    chObj = chList[0]

    bRet, channelId = jsonGetKeyValue(chObj, 'channelId')
    if bRet == False : return False
    bRet, channelIcon = jsonGetKeyValue(chObj, 'imgUrl')
    if bRet == False : return False
    bRet, channelName = jsonGetKeyValue(chObj, 'channelName')
    channelName = str(channelName.encode('utf8'))
    if bRet == False : return False
    bRet, channelNumber = jsonGetKeyValue(chObj, 'channelNumber')
    if bRet == False : return False

    return True, channelId, channelIcon, channelName, channelNumber


def launchApp( appId, params = None ) :
    api = 'luna://com.palm.applicationManager/launch'
    payload = {
        "id": appId
    }
    if params :
        payload["params"] = params

    ret = lunaCommand( api, payload )
    #print(ret)
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    return bRet

def getUCMAppCount( appId, day=-56, moreThan = 10 ) :
    api = 'luna://com.webos.service.usercontextmanager/getHistory'
    payload = {
        "eventType": "app",
        "eventId": appId,
        "fromDate": convert2YYYYMMDD(day),
        "moreThan": moreThan,
        "limit": 1
    }
    ret = lunaCommand( api, payload )
    #print(ret)
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, totalCount = jsonGetKeyValue( retObj, "totalCount")
    if bRet == False : return False

    return totalCount

def getUCMChannelCount( channelId=None, day=-14 ) :
    api = 'luna://com.webos.service.usercontextmanager/getHistory'
    if channelId :
        payload = {
            "eventType": "channel",
            "eventId": channelId,
            "fromDate": convert2YYYYMMDDOfBroadcast(day),
            "limit": 1
        }
    else :
        payload = {
            "eventType": "channel",
            "fromDate": convert2YYYYMMDDOfBroadcast(day),
            "limit": 1
        }

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, totalCount = jsonGetKeyValue( retObj, 'totalCount')
    if bRet == False : return False

    return totalCount

def putUCMLog1( kind, evtId, startTime, endTime, detail = True ):
    # get Current timestamp

    api = 'luna://com.palm.db/put'
    global currAccount
    payload = {
        "objects": [{
            "loginId" : "",
            # mlt4tv #158 verified
            "loginUserNum" : currAccount,
            "_kind": kind,
            "eventId": evtId,
            "startTimeStamp": startTime,
            "endTimeStamp": endTime
        }]
    }

    ret = lunaCommand( api, payload, sender='com.webos.service.usercontextmanager' )
    #print(ret)
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if detail :
        print('[INFO] Put UCM Log (%s, %d, %d - %d) : %r' (kind, evtId, st, et, bRet ))
    return bRet

def putUCMLog( kind, evtId, day=0, hour=0, minute=0, second=0 ):
    # get Current timestamp
    t = time.localtime()
    et = int(convert2Timestamp(t))
    et = et + day*24*60*60
    et = et + hour*60*60
    et = et + minute*60
    et = et + second
    st = et - 10*60

    bRet = putUCMLog1( kind, evtId, st, et, detail = False )
    print('[INFO] Put UCM Log (%s, %s, %d - %d) : %r' % (kind, evtId, st, et, bRet ))
    return bRet

def reloadUCMDB() :
    # luna-send -n 1 -f luna://com.webos.service.usercontextmanager/test '{"num":4001}'
    api = 'luna://com.webos.service.usercontextmanager/test'
    payload = {"num":4001}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('[INFO] Reload UCM DB : ', bRet)
    time.sleep(1)
    return bRet;

def clearUCMDB( kind ):
    # luna-send -n 1 -a com.webos.service.nudge -f luna://com.palm.db/del '{"query":{"from":"com.webos.service.nudge.history:1"}}'
    api = 'luna://com.palm.db/del'
    payload = {
        "query": {
            "from": kind
        }
    }
    ret = lunaCommand( api, payload, sender = 'com.webos.service.usercontextmanager' )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('[INFO] Clear UCM DB (%s) : %r' % ( kind, bRet ))
    return bRet;

def displayUCMDB( kind, pageId = None, detail = True ):
    # luna-send -n 1 -f luna://com.palm.db/find '{"query":{"from":"com.webos.service.nudge.history:1"},"count":true}'

    api = 'luna://com.palm.db/find'
    payload = {
        "query": {
            "from": kind
        },
        "count": True
    }
    if pageId :
        payload["query"]["page"] = pageId

    ret = lunaCommand( api, payload )
    #print(ret)
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, count = jsonGetKeyValue( retObj, "count")
    if bRet == False : return False

    print("[INFO] Display UCM DB for ", kind)
    print("         count : ", count)
    bRet, nextPage = jsonGetKeyValue( retObj, "next")
    print("         next  : ", nextPage)

    bRet, jResults = jsonGetKeyValue( retObj, "results")
    i = 0;
    #print(bRet, jResults)
    for obj in jResults:
        i=i+1
        bRet, st = jsonGetKeyValue( obj, "startTimeStamp")
        if bRet == False : continue
        bRet, et = jsonGetKeyValue( obj, "endTimeStamp")
        if bRet == False : continue
        bRet, _id = jsonGetKeyValue( obj, "eventId")
        if bRet == False : continue

        if detail == True :
            print('%8d/%-8d> %-20s(%d) ~ %-20s(%d) / eventID: %s' % ( i, count,
                    convert2Date(st), st, convert2Date(et), et, _id))

    if nextPage :
        displayUCMDB( kind, nextPage )

    if pageId == None :
        print('[INFO] Display all UCM DB (Total %d Items)' % count)

    return True;

def reloadHistoryDB() :
    # luna-send -n 1 -f luna://com.webos.service.nudge/requestNudge '{"nudgeId":"historyTest_0"}'
    api = 'luna://com.webos.service.nudge/requestNudge'
    payload = {"nudgeId":"historyTest_0"}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('[INFO] Reload History DB : ', bRet)
    #time.sleep(1)
    return bRet;

def clearHistoryDB():
    # luna-send -n 1 -a com.webos.service.nudge -f luna://com.palm.db/del '{"query":{"from":"com.webos.service.nudge.history:1"}}'

    api = 'luna://com.palm.db/del'
    payload = {
        "query": {
            "from": "com.webos.service.nudge.history:1"
        }
    }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('[INFO] Clear History DB : ', bRet)
    return bRet;

def displayHistoryDB( pageId = None ):
    # luna-send -n 1 -f luna://com.palm.db/find '{"query":{"from":"com.webos.service.nudge.history:1"},"count":true}'

    api = 'luna://com.palm.db/find'
    payload = {
        "query": {
            "from": "com.webos.service.nudge.history:1"
        },
        "count": True
    }
    if pageId :
        payload["query"]["page"] = pageId

    ret = lunaCommand( api, payload )
    #print(ret)
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, count = jsonGetKeyValue( retObj, "count")
    if bRet == False : return False

    print("[INFO] Display History DB")
    print("         count : ", count)
    bRet, nextPage = jsonGetKeyValue( retObj, "next")
    print("         next  : ", nextPage)


    bRet, jResults = jsonGetKeyValue( retObj, "results")
    i = 0;
    #print(bRet, jResults)
    for obj in jResults:
        i=i+1
        bRet, _account = jsonGetKeyValue( obj, "account")
        # if bRet == False : continue
        bRet, _timeStamp = jsonGetKeyValue( obj, "timeStamp")
        if bRet == False : continue
        bRet, _state = jsonGetKeyValue( obj, "state")
        if bRet == False : continue
        bRet, _result = jsonGetKeyValue( obj, "result")
        if bRet == False : continue
        bRet, _id = jsonGetKeyValue( obj, "id")
        if bRet == False : continue

        print('%8d/%-8d> A:<%-20s> %-20s(%d) %-12s %-12s %s' % ( i, count,
                _account,
                convert2Date(_timeStamp), _timeStamp, convertNudgeState(_state),
                convertNudgeResult(_result), _id))

    if nextPage :
        displayHistoryDB( nextPage )

    if pageId == None :
        print('[INFO] Display all History DB (Total %d Items)' % count)

    return True;

def insertHistory(nudgeId, timeStamp, result, state,
        day = 0, hour = 0, minute = 0, second = 0, account = None):
    # luna-send -n 1 -a com.webos.service.nudge -f luna://com.palm.db/put '{"objects":[{"_kind":"com.webos.service.nudge.history:1", "id": "test_id_1", "timeStamp": 1491095645, "result":0, "state":0}]}'

    global currAccount
    if account is None:
        account = currAccount

    recommend1day_nudges = [ 'nu_tv_on_magic', 'nu_tv_on_BT_surround', 'nu_tv_on_livepick' ]

    if type(timeStamp) is time.struct_time :
        timeStamp = convert2Timestamp(timeStamp)

    timeStamp = int(timeStamp);
    timeStamp = timeStamp + day*(60*60*24)
    timeStamp = timeStamp + hour*(60*60)
    timeStamp = timeStamp + minute*(60)
    timeStamp = timeStamp + second


    api = 'luna://com.palm.db/put'
    payload = {
        "objects": [{
            "_kind": "com.webos.service.nudge.history:1",
            "account" : account,
            "id": nudgeId,
            "timeStamp": timeStamp,
            "result": convertNudgeResult(result),
            "state": convertNudgeState(state)
        }]
    }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('[INFO] Insert History    : ', bRet, 'id: ', nudgeId)

    if nudgeId in recommend1day_nudges:
        return insertHistory( 'recommendOnceADayGroup', timeStamp, "SELECTED", "READY" )
    return bRet;


def getHistoryState(nudgeId) :
    # luna-send -n 1 -a com.webos.service.nudge -f luna://com.palm.db/find '{"query":{"where":[{"prop":"id","op":"=","val":"nu_tv_on_1"}],"from":"com.webos.service.nudge.  history:1", "desc" : true, "limit" : 1}}'
    # luna-send -n 1 -a com.webos.service.nudge -f luna://com.palm.db/search '{"query":{"where":[{"prop":"id","op":"=","val":"nu_tv_on_1"}],"from":"com.webos.service.nudge.history:1", "desc" : true, "orderBy" : "timeStamp", "limit" : 1}}'


    api = 'luna://com.palm.db/search'
    payload = {
        "query": {
            "where": [{
                "prop": "id",
                "op": "=",
                "val": nudgeId
            }],
            "from": "com.webos.service.nudge.history:1",
            "desc": True,
            "orderBy" : "timeStamp",
            "limit": 1
        }
    }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    nudgeState = None
    bRet, jResults = jsonGetKeyValue( retObj, "results")
    if jResults :
        bRet, nudgeState = jsonGetKeyValue( jResults[0], "state")
        print('[INFO] STATE %s : %s' % (nudgeId, convertNudgeState(nudgeState)))
        return True

    print('[INFO] STATE %s : %s' % (nudgeId, nudgeState))
    return False


def requestRelayNudge( msg, params = {} ):
    api = 'luna://com.webos.service.nudge/globalNudgeEmitter/requestRelayNudge'
    payload = {
        "nudgeId" : "TEST",
        "message" : msg,
        "params" : params
    }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    return bRet


def resetGlobalNudgeEmitter():
    bRet = requestRelayNudge( "ResetNudgeState" );
    if bRet == False : return False
    bRet = requestRelayNudge( "ResetTVReady" );
    if bRet == False : return False
    print('[INFO] Reset GlobalNudgeEmitter')
    return True

def getChannelList( channelMode = "" ):
    List = []

    channelKey = 'channelNumber'
    if channelMode == "" or channelMode == "IP":
        channelKey = 'channelId'

    api = 'luna://com.webos.service.iepg/getChannelList'
    payload = {
        "dataType": 0,
        "sort": 0,
        "channelGroup": ["All"],
        "channelMode": channelMode
    }
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return List

    bRet, jChannels = jsonGetKeyValue( retObj, "channelList")
    if bRet == False : return List

    for obj in jChannels:
        bRet, st = jsonGetKeyValue( obj, channelKey )
        if bRet == False : continue

        bRet, tcn = jsonGetKeyValue( obj, "channelName" )
        if bRet == False : continue
        if len(tcn) == 0 : continue

        List.append( st )

    return List

def getAppList():
    List = []

    api = 'luna://com.webos.applicationManager/listApps'
    payload = {}

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, jApps = jsonGetKeyValue( retObj, "apps")
    if bRet == False : return False

    for obj in jApps:
        bRet, _id = jsonGetKeyValue( obj, "id")
        if bRet == False : continue
        List.append( _id )

    return List

def fillUCMLog( kind ,tarLists, count = 50, usingTime = 60*60, margineTime = 0,
        startTimeDelta = -56*24*60*60, endTimeDelta = 0 ) :

    if len(tarLists) <= 0 :
        return;

    try :
        print('\n%s / default LogCount : %d' % (kind, count))
        iv = int(input(' >> input requied log count : '))
    except SyntaxError:
        iv = 50
    except ValueError:
        iv = 50
    count = iv

    t = time.localtime()
    et = int(convert2Timestamp(t))
    st = et + startTimeDelta

    offset = st

    # for LiveTV demo
    adjust = 0
    if kind == UCM_LIVE_KIND :
        adjust = 10

    llen = len(tarLists)

    for i in range(count):
        _st = offset
        _et = offset+usingTime
        offset = _et + margineTime
        if _et > et :
            break

        # > exception handle
        if i+adjust >= llen :
            adjust = -i

        _id = tarLists[i+adjust]

        print('%8d/%-8d> %-20s(%d) ~ %-20s(%d) / eventID: %s' % ( i+1, count,
                convert2Date(_st), st, convert2Date(_et), et, _id))
        putUCMLog1( kind, _id, _st, _et, detail = False )

    print('[INFO] Total %d item add to UCM Log %s' % (count, kind ))

    return

def generateUCMBase( typeChannel = True, typeApp = True ):

    if typeChannel == True :
        lst = getChannelList()
        #lst = []
        #lst.append('3_82_11_1_0_0_0')

        fillUCMLog( UCM_LIVE_KIND, lst, usingTime = 5*60*60, margineTime=30*60)

        lst = getChannelList("STB")
        fillUCMLog( UCM_STB_KIND, lst, usingTime = 7*60*60, margineTime=30*60)

    if typeApp == True :
        #lst = getAppList()
        lst = []
        lst.append( 'com.webos.app.browser' )
        fillUCMLog( UCM_APP_KIND, lst, count = 100, usingTime = 60*60, margineTime = 11*60*60)

    reloadUCMDB()
    return

def displayNudgeState():
    api = 'luna://com.webos.service.nudge/getNudgeState'
    payload = {}

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False

    bRet, jNudges = jsonGetKeyValue( retObj, "nudgeState")
    if bRet == False : return False

    i = 0
    print('-----< nudge state >----')
    for obj in jNudges:
        i=i+1
        bRet, _id = jsonGetKeyValue( obj, "id")
        if bRet == False : continue
        bRet, _state = jsonGetKeyValue( obj, "state")
        print('%8d > %-30s : %s' % ( i, _id, _state))
    print('------------------------')
    return True

def displayGlobalNudgeState():
    bRet = requestRelayNudge( "DisplayNudgeState" );
    if bRet == False : return False
    return True

def setNudgeState():
    nId = input(' >> Input nudgeId : ')
    nSt = 0
    try :
        print(' <*> 0: Ready, 1: Suspend, 2:Terminate')
        nSt = int(input(' >> Input nudge state(default:0) : '))
    except SyntaxError:
        nSt = 0
    except ValueError:
        nSt = 0

    if nSt == 1:
        insertHistory(nId, time.localtime(), "SELECTED", "SUSPENDED" )
        print(' + [%s] -> SUSPENDED ' % nId)
    elif nSt == 2:
        insertHistory(nId, time.localtime(), "SELECTED", "TERMINATED"  )
        print(' + [%s] -> TERMINATED ' % nId)
    else :
        insertHistory(nId, time.localtime(), "SELECTED", "READY" )
        print(' + [%s] -> READY ' % nId)

    reloadHistoryDB()

def generateDummyServerConfiguration():
    os.system('mkdir /mnt/lg/cmn_data/nudge')
    os.system('echo \'{ "returnValue": true, "serverResponse": { "code": "200", "message": "OK", "response": "{\\"nudgeDetails\\":[]}" } }\' > /mnt/lg/cmn_data/nudge/nudgeConfiguration.json')

#====< TEST Framework >>>>>
def doVerifyLog( logFilter, unitId, unitTargetlog, unitTrigger, unitTimeout ) :
    v = LogVerifier(key = logFilter)
    unitTrigger[0](*unitTrigger[1:])
    bRet = v.checkLog( unitTargetlog, unitTimeout )
    return bRet

def makeUnitTest( uId, preConditions, postConditions, targetLog, trigger, timeout = 5 ):
    # type : funcTuple = ( func, arg1, arg2, ..., arg n )
    unitTest = {}
    unitTest['id'] = uId

    # set pre condition
    unitTest['preConditions'] = preConditions     # [ funcTuple, ... ]

    # set post condition
    unitTest['postConditions'] = postConditions   # [ funcTuple, ... ]

    unitTest['targetLog'] = targetLog
    unitTest['trigger'] = trigger               # [ funcTuple, ... ]
    unitTest['timeout'] = 5
    return unitTest


def testFramework_baseLog( testConfig ):
    '''
    {
        "LogFilter" : " NUDGE ",
        "ConfigId" : "testConfig1",
        "GlobalPreConditions" : [ globalPreFunc, ... ],
        "UnitTest" : [
        {
            "id" : "test1"
            "preConditions" : [ unitPreFunc, ... ],
            "postConditions" : [ unitPostFunc, ... ],
            "targetLog" : "HELLO ...",
            "trigger" : tirggerFunc
            "timeout" : 5
            "UnitResult" : True/False
        },
        {
            ...
        }
        ]

        "GlobalPostConditions" : [ globalPostFunc, ... ],
    }
    '''

    logFilter = testConfig["LogFilter"]

    # run global pre condition
    globalPreConditions = testConfig["GlobalPreConditions"]
    print('[GLOBAL PRE-CONDITON]')
    for gPreFunc in globalPreConditions:
        gPreFunc[0](*gPreFunc[1:])

    for unitTest in testConfig['UnitTest']:
        unitId              = unitTest["id"]
        unitPreConditions   = unitTest["preConditions"]
        unitPostConditions  = unitTest["postConditions"]
        unitTargetLog       = unitTest["targetLog"]
        unitTriggerFunc     = unitTest["trigger"]
        # default test timeout
        unitTimeout         = 5
        if "UnitTimeout" in unitTest:
            unitTimeout         = int(unitTest["UnitTimeout"])

        for unitPreFunc in unitPreConditions:
            unitPreFunc[0](*unitPreFunc[1:])

        # do - test
        unitTest['UnitResult'] = doVerifyLog( logFilter, unitId, unitTargetLog,
                                                unitTriggerFunc, unitTimeout )
        print('[DO TEST] RESULT({}) for UNIT TEST <{}>'.format( unitTest['UnitResult'], unitId ))

        for unitPostFunc in unitPostConditions:
            unitPostFunc[0](*unitPostFunc[1:])

        #
        time.sleep(1)

    # run post condition
    globalPostConditions = testConfig["GlobalPostConditions"]
    for gPostFunc in globalPostConditions:
        gPostFunc[0](*gPostFunc[1:])

#<<<<< TEST Framework ======

def unitTest4CaseCondition():
    # testcase loc for caseCondtion : /mnt/lg/cmn_data/nudge/caseConditions/
    params = {
        "testcases": [{
            "id": "nu_tc_caseCond_ok",
            "expect": True,
        },
        {
            "id": "nu_tc_caseCond_ng_1",
            "expect": False,
        },
        {
            "id": "nu_tc_caseCond_ng_2",
            "expect": False,
        },
        {
            "id": "nu_tc_caseCond_ng_3",
            "expect": False,
        },
        {
            "id": "nu_tc_caseCond_ng_4",
            "expect": False,
        }]
    }
    requestRelayNudge( "caseCondition_test", params );

def testcase4Recommend1DayGroup( tcId, nudge, trigerFunc, logString, day=0, hour=0, minute=0):
    r1dKey = 'recommendOnceADayGroup'

    # make nudge generate-condition
    trigerFunc()

    # insert recommendOnceADayGroup history to history
    insertHistory( r1dKey, time.localtime(), "SELECTED", "READY", day, hour, minute )
    reloadHistoryDB()
    displayHistoryDB(None)

    #v = LogVerifier(key = "nudge [")   # for webOS4.5
    v = LogVerifier(key = " NUDGE ")   # for webOS5.0
    resetGlobalNudgeEmitter()
    bRet = v.checkLog( logString )

    retString = ""
    if bRet == True :
        print(' * PASS : TC(%s) RESULT : %r' % (tcId, bRet))
        retString = "PASS"
    else :
        print(' * FAIL : TC(%s) RESULT : %r' % (tcId, bRet))
        retString = "NG"

    # post Action
    time.sleep(1)
    enterKey("EXIT")

    # return result
    return retString

def unitTest4Recommend1DayGroup() :
    reports = list()
    nudge = "nu_tv_on_magic"

    tcId = "recommend-T01-Reject"
    result = testcase4Recommend1DayGroup( tcId, nudge, nu_tv_on_magic,
            "NUDGE(%s) REJECT -> TV_ON_RECOMMEND_GROUP_INTERVAL" % nudge, minute=-5 )
    reports.append( (tcId, result) )

    tcId = "recommend-T02-Reject"
    result = testcase4Recommend1DayGroup( tcId, nudge, nu_tv_on_magic,
            "NUDGE(%s) REJECT -> TV_ON_RECOMMEND_GROUP_INTERVAL" % nudge, minute=-20 )
    reports.append( (tcId, result) )

    tcId = "recommend-T03-Reject"
    result = testcase4Recommend1DayGroup( tcId, nudge, nu_tv_on_magic,
            "NUDGE(%s) REJECT -> TV_ON_RECOMMEND_GROUP_INTERVAL" % nudge, hour=-23 )
    reports.append( (tcId, result) )

    tcId = "recommend-T04-Reject"
    result = testcase4Recommend1DayGroup( tcId, nudge, nu_tv_on_magic,
            "NUDGE(%s) REJECT -> TV_ON_RECOMMEND_GROUP_INTERVAL" % nudge, hour=-23, minute=-59 )
    tcId = "recommend-T10-Accept"
    result = testcase4Recommend1DayGroup( tcId, nudge, nu_tv_on_magic,
            "NUDGE(%s) ACCEPT" % nudge, hour=-25 )
    reports.append( (tcId, result) )

    tcId = "recommend-T11-Accept"
    result = testcase4Recommend1DayGroup( tcId, nudge, nu_tv_on_magic,
            "NUDGE(%s) ACCEPT" % nudge, day=-30 )
    reports.append( (tcId, result) )

    # print(report)
    print('\n\n----< REPORT >----')
    for key, val in reports:
        print(' * TC: [%s] : %s' % (key, val))

    print('------------------\n')

def testConfig4_testHomeLaunch_negative() :
    # make testConfig
    testConfig = {}

    testConfig['LogFilter'] = ' NUDGE '
    testConfig['ConfigId']  = 'CaseTest: HomeAutoLaunch = on'
    testConfig['GlobalPreConditions'] = []
    testConfig['GlobalPreConditions'].append( (setSettings, 'general', 'homeAutoLaunch', 'on') )
    testConfig['GlobalPreConditions'].append( (runSystem, 'PmLogCtl set NUDGE info') )
    testConfig['GlobalPostConditions'] = []
    testConfig['UnitTest'] = []

    unitTest = makeUnitTest( 'T02-REJECT-nu_tv_on_magic', [(nu_tv_on_magic,)], [(enterKey, "EXIT")],
            'REJECT : case-conditions (title : settings_homeAutoLaunch_off), nudge(nu_tv_on_magic)',
            (resetGlobalNudgeEmitter,), 10 );
    testConfig['UnitTest'].append(unitTest)

    unitTest = makeUnitTest( 'T03-REJECT-nu_tv_on_1', [(nu_tv_on_1,)], [(enterKey, "EXIT")],
            'REJECT : case-conditions (title : settings_homeAutoLaunch_off), nudge(nu_tv_on_1)',
            (resetGlobalNudgeEmitter,), 10 );
    testConfig['UnitTest'].append(unitTest)

    unitTest = makeUnitTest( 'T04-REJECT-nu_tv_on_1_6item', [(nu_tv_on_1_6item,)], [(enterKey, "EXIT")],
            'REJECT : case-conditions (title : settings_homeAutoLaunch_off), nudge(nu_tv_on_1_6item)',
            (resetGlobalNudgeEmitter,), 10 );
    testConfig['UnitTest'].append(unitTest)

    testFramework_baseLog( testConfig )
    return testConfig

def testConfig4_testHomeLaunch_positive() :
    # make testConfig
    testConfig = {}

    testConfig['LogFilter'] = ' NUDGE '
    testConfig['ConfigId']  = 'CaseTest: HomeAutoLaunch = off'
    testConfig['GlobalPreConditions'] = []
    testConfig['GlobalPreConditions'].append( (setSettings, 'general', 'homeAutoLaunch', 'off') )
    testConfig['GlobalPreConditions'].append( (runSystem, 'PmLogCtl set NUDGE info') )
    testConfig['GlobalPostConditions'] = []
    testConfig['UnitTest'] = []

    unitTest = makeUnitTest( 'T02-ACCEPT-nu_tv_on_magic', [(nu_tv_on_magic,)], [(enterKey, "EXIT")],
            'NUDGE(nu_tv_on_magic) ACCEPT',
            (resetGlobalNudgeEmitter,), 10 );
    testConfig['UnitTest'].append(unitTest)
    unitTest = makeUnitTest( 'T03-ACCEPT-nu_tv_on_1', [(nu_tv_on_1,)], [(enterKey, "EXIT")],
            'NUDGE(nu_tv_on_1) ACCEPT',
            (resetGlobalNudgeEmitter,), 10 );
    testConfig['UnitTest'].append(unitTest)
    unitTest = makeUnitTest( 'T04-ACCEPT-nu_tv_on_1_6item', [(nu_tv_on_1_6item,)], [(enterKey, "EXIT")],
            'NUDGE(nu_tv_on_1_6item) ACCEPT',
            (resetGlobalNudgeEmitter,), 10 );
    testConfig['UnitTest'].append(unitTest)

    testFramework_baseLog( testConfig )
    return testConfig

def unitTest4HomeLaunchforTVOnNudge() :
    reports = []
    ret = testConfig4_testHomeLaunch_negative()
    reports.append(ret)

    ret = testConfig4_testHomeLaunch_positive()
    reports.append(ret)

    # print(report)
    print('\n\n----< REPORT >----')
    for testConfig in reports:
        configId = testConfig['ConfigId']
        for unit in testConfig['UnitTest']:
            tId = unit['id']
            result = unit['UnitResult']
            print('RESULT : {}\t, TEST_ID : {} / {}'.format( result, configId, tId))
    print('------------------\n')

#==============================================================================

def nu_start( verifyString = False):
    if verifyString == True :
        clearHistoryDB()
        reloadHistoryDB()
        resetGlobalNudgeEmitter()
        return True

    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    reloadUCMDB()

    clearHistoryDB()
    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please turn off EULA")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_3(verifyString = False):
    if verifyString == True :
        clearHistoryDB()
        insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
        insertHistory("nu_tv_on_3", time.localtime(), "SELECTED", "READY", day=-29 )
        reloadHistoryDB()
        resetGlobalNudgeEmitter()
        return True

    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED", "READY", day=-29 )
    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please turn on EULA")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_magic(verifyString = False):
    if verifyString == True :
        clearHistoryDB()
        insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
        insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
        insertHistory("nu_tv_on_magic", time.localtime(), "SELECTED", "READY", day=-28 )
        insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
        insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
        insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )
        reloadHistoryDB()
        resetGlobalNudgeEmitter()
        return True

    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
    insertHistory("nu_tv_on_magic", time.localtime(), "SELECTED", "READY", day=-28 )
    insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
    insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )

    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_livepick(verifyString = False):
    if verifyString == True :
        clearHistoryDB()
        insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
        insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
        insertHistory("nu_tv_on_magic", time.localtime(), "SELECTED", "TERMINATED", day=-28 )
        insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
        insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "READY", day=-26 )
        insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )
        reloadHistoryDB()
        resetGlobalNudgeEmitter()
        return True

    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
    insertHistory("nu_tv_on_magic", time.localtime(), "SELECTED", "TERMINATED", day=-28 )
    insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "READY", day=-26 )
    insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )

    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_BT_surround(verifyString = False):
    if verifyString == True :
        clearHistoryDB()
        insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
        insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
        insertHistory("nu_tv_on_magic", time.localtime(), "SELECTED", "TERMINATED", day=-28 )
        insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
        insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
        insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "READY", day=-25 )
        reloadHistoryDB()
        resetGlobalNudgeEmitter()
        return True

    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
    insertHistory("nu_tv_on_magic", time.localtime(), "SELECTED", "TERMINATED", day=-28 )
    insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
    insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "READY", day=-25 )

    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_1_6item( verifyString = False):
    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    generateUCMBase()
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-31 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-30 )
    insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-29 )
    insertHistory("nu_tv_on_1_6item", time.localtime(), "SELECTED", "READY", day=-28 )

    insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
    insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )

    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_1( verifyString = False):
    if verifyString == True :
        clearHistoryDB()
        insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
        insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
        insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-28 )
        insertHistory("nu_tv_on_1_6item", time.localtime(), "CLOSED",  "TERMINATED", day=-27 )
        insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
        insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )
        insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-22 )

        insertHistory("nu_tv_on_1", time.localtime(), "SELECTED", "READY", day=-10 )
        reloadHistoryDB()
        resetGlobalNudgeEmitter()
        return True

    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    generateUCMBase()
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
    insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-28 )
    insertHistory("nu_tv_on_1_6item", time.localtime(), "CLOSED",  "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-26 )
    insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-25 )
    insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-22 )

    insertHistory("nu_tv_on_1", time.localtime(), "SELECTED", "READY", day=-26 )

    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()

def nu_tv_on_complete( verifyString = False, pushUCMLog = True):
    if verifyString == True :
        clearHistoryDB()
        insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
        insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
        insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-28 )
        insertHistory("nu_tv_on_1_6item", time.localtime(), "CLOSED",  "TERMINATED", day=-27 )
        insertHistory("nu_tv_on_1", time.localtime(), "CLOSED",  "TERMINATED", day=-26 )
        insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-25 )
        insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-24 )
        insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-23 )

        reloadHistoryDB()
        return True

    if pushUCMLog == True:
        clearUCMDB( UCM_APP_KIND)
        clearUCMDB( UCM_LIVE_KIND)
        clearUCMDB( UCM_STB_KIND)
        generateUCMBase()
        reloadUCMDB()
        displayUCMDB(UCM_APP_KIND, detail = False)
        displayUCMDB(UCM_LIVE_KIND, detail = False)
        displayUCMDB(UCM_STB_KIND, detail = False)

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
    insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-28 )
    insertHistory("nu_tv_on_1_6item", time.localtime(), "CLOSED",  "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_1", time.localtime(), "CLOSED",  "TERMINATED", day=-26 )
    insertHistory("nu_airplay", time.localtime(), "SELECTED", "TERMINATED", day=-25 )
    insertHistory("nu_tv_on_livepick", time.localtime(), "SELECTED", "TERMINATED", day=-24 )
    insertHistory("nu_tv_on_BT_surround", time.localtime(), "SELECTED", "TERMINATED", day=-23 )
    reloadHistoryDB()

    displayHistoryDB(None)

def nu_amazon_entry(verifyString = False):
    if verifyString == True :
        # exit to liveTV
        enterKey("EXIT")
        time.sleep(2)
    nu_tv_on_complete(verifyString)
    insertHistory("nu_amazon_entry", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    if verifyString :
        launchApp("amazon")
        time.sleep(3)
        return
    print(" -----------------------------------------")
    print(" * Launch amazon app")
    if bAutomatic : launchApp("amazon")

def nu_voice_entry():
    nu_tv_on_complete()
    insertHistory("nu_voice_entry", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()

    print(" -----------------------------------------")
    print(" * [NOTICE] NOT SUPPORT ANY MORE")
    return

    appId = 'com.webos.app.voiceview'
    count = getUCMAppCount( appId )
    freq = 6    # ref. nudge description
    remain = count % freq
    reqCount = freq - remain - 1    # for lastApp

    for i in range(reqCount):
        putUCMLog( UCM_APP_KIND, appId, day = -10, hour= -10+i)

    reloadUCMDB()
    count = getUCMAppCount( appId )
    print('[INFO] AppId(%s), Frequency(%d), UCM_DB_LOG_COUNT(%d)' % (appId, freq, count))

    print(" -----------------------------------------")
    print(" * Launch voice app (using over than 10 sec) and exit")
    if bAutomatic : launchApp(appId)

def nu_app_entry(appId, verifyString = False):
    if verifyString == True :
        # exit to liveTV
        enterKey("EXIT")
        time.sleep(2)

    nu_tv_on_complete(verifyString)
    insertHistory("nu_app_entry", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()

    print(" -----------------------------------------")
    print(' * Try launch app(%s)' % appId)
    count = getUCMAppCount( appId, moreThan = 600 )
    freq = 12    # ref. nudge description
    remain = count % freq
    reqCount = freq - remain        # for currApp

    for i in range(reqCount):
        putUCMLog( UCM_APP_KIND, appId, day = -7, hour= -10+i)

    reloadUCMDB()
    reloadHistoryDB()
    count = getUCMAppCount( appId, moreThan = 600 )
    print('[INFO] AppId(%s), Frequency(%d), UCM_DB_LOG_COUNT(%d)' % (appId, freq, count))

    print(" -----------------------------------------")
    print(" * Check QuickAccess 0-long press (already resistered app)")
    print(" * Launch App(%s)" % appId)
    if bAutomatic : launchApp(appId)
    elif verifyString :
        launchApp(appId)
        time.sleep(2)

def nu_setting_off(verifyString = False):
    if verifyString == False :
        clearUCMDB( UCM_APP_KIND)
        clearUCMDB( UCM_LIVE_KIND)
        clearUCMDB( UCM_STB_KIND)
        generateUCMBase()
        reloadUCMDB()

    # nudge setting -> on
    api = 'luna://com.webos.settingsservice/setSystemSettings'
    payload = {"category": "general", "settings": {"aiNudge" : "on"}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)

    clearHistoryDB()
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-30 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-29 )
    insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-28 )
    insertHistory("nu_tv_on_1_6item", time.localtime(), "CLOSED",  "TERMINATED", day=-27 )
    insertHistory("nu_tv_on_1", time.localtime(), "SELECTED",  "TERMINATED", day=-26 )

    insertHistory("nu_setting_off", time.localtime(), "SELECTED",  "READY", day=-20 )


    # DONE : insert more than 150 nudges
    for i in range(150):
        insertHistory("nu_tv_on_1", time.localtime(), "CLOSED",  "TERMINATED", day=-25, hour = i )
    insertHistory("nu_ch_zapping", time.localtime(), "SELECTED",  "READY", day=-18 )

    reloadHistoryDB()

    if verifyString == False :
        displayHistoryDB(None)
        print(" -----------------------------------------")
        print(' # luna-send -n 1 -f luna://com.webos.service.nudge/requestNudge \'{ "nudgeId": "nu_instance", "items": [{ "message": "Test> Close or Wait for timeout(DO NOT REGISTER ISSUE for LOCALE STRING. IT IS NOT BUG)", "button": "YES", "type": "Text" }] }\' ')

    api = 'luna://com.webos.service.nudge/requestNudge'
    payload = {
        "nudgeId": "nu_instance",
        "items": [{
            "message": "Test> Close or Wait for timeout(DO NOT REGISTER ISSUE for LOCALE STRING. IT IS NOT BUG)",
            "button": "YES",
            "type": "Text"
        }]
    }

    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)


    if verifyString == True :
        print(' > zapping nudge displayed -> wait 3 sec')
        time.sleep(3)
        print(' > press exit key -> wait 2 sec')
        enterKey("EXIT")
        time.sleep(2)

    # CHECK nudge nu_setting_off

def nu_setting_on(verifyString = False):
    # nudge setting -> off
    api = 'luna://com.webos.settingsservice/setSystemSettingFactoryValue'
    payload = {"category": "general", "settings": {"aiNudge" : "off"}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)

    # nudge setting -> on
    api = 'luna://com.webos.settingsservice/setSystemSettings'
    payload = {"category": "general", "settings": {"aiNudge" : "off"}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)

    clearHistoryDB()
    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")
    print(" <*> Doesn't support AUTO mode.")

    if bAutomatic :
        resetGlobalNudgeEmitter()
        return True

    if verifyString == True :
        resetGlobalNudgeEmitter()
        return True

def nu_ch_watch_tv_n_times():
    nu_tv_on_complete()
    insertHistory("nu_ch_watch_tv_n_times", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()

    if checkSTBApp() == True :
        print(" * STB")
        print(' * > NOT SUPPROT')
        return False

    zappingValidRatio = 1
    historyCheckCount = 1
    if checkLiveTV() == True :
        print(" * Live")
        bRet, channelId, channelIcon, channelName, channelNumber = getLiveTVChannelInfo()
        if bRet == False : return False
        count = 1
        try :
            count = int(input(' >> input log count of current channel (current log count {}) : '.format(getUCMChannelCount(channelId))))
        except:
            count = 1

        for i in range(count) :
            putUCMLog(UCM_LIVE_KIND, channelId,  day = -10, hour= -10)

        reloadUCMDB()

        historyCheckCount = getUCMChannelCount(channelId)
        totalCount = getUCMChannelCount()
        if totalCount < 1 or historyCheckCount < 1 :
            print('  > current channel log count error : {}'.format(channelId, historyCheckCount))
            print('  > total log count error : {}'.format(totalCount))
            return False

        ratio = math.trunc(historyCheckCount/totalCount*100)
        zappingValidRatio = min(max(ratio - 0.1, 1), 20)
        try :
            zappingValidRatio = int(input(' >> input zapping valid ratio (less than {}) : '.format(zappingValidRatio)))
        except:
            zappingValidRatio = 1
        try :
            historyCheckCount = int(input(' >> input zapping history check count (current log count {}) : '.format(historyCheckCount)))
        except:
            historyCheckCount = 1
    else :
        print(' > This test is valid Live TV App')
        return False

    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"com.webos.app.livetv", "params": {"id": "testNudge", "zappingValidRatio": %d, "historyCheckCount" : %d}}\' ' %(zappingValidRatio, historyCheckCount))

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":"com.webos.app.livetv", "params": {"id": "testNudge", "zappingValidRatio": zappingValidRatio, "historyCheckCount" : historyCheckCount}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)

    if bRet == False : return False
    print('  > automatic : ', bAutomatic)
    if bAutomatic == False :
        print('  > You might see the nudge in 10 seconds after doing channel up and down')
        return True

    print('  > TV will do channel up and do channel down, and then you might see the nudge after 10 seconds')
    lunaCommand('luna://com.webos.service.networkinput/controls/channelUp', {})
    time.sleep(3)
    lunaCommand('luna://com.webos.service.networkinput/controls/channelDown', {})

    return True

def checkInputcommonAppId(appId = None):
    if checkLiveTV(appId) == True or checkSTBApp(appId) == True:
        return True
    print(' > This test is valid Live TV App or STB App')
    return False

def nu_ch_zapping():
    nu_tv_on_complete()
    insertHistory("nu_ch_zapping", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    print(" -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "zappingCount": 1, "zappingTime": 1}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "zappingCount": 1, "zappingTime": 1}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False
    print('  > You might see the nudge after changing any channel and watching the channel for 10 seconds')
    return True

def nu_AI_channel_zapping():
    nu_tv_on_complete()
    insertHistory("nu_AI_channel_zapping", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    
    # print(f'----------------{bRet} {appId} ------------')
    
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    program, vod, ott = setTestCountAiChannel()

    print("\n -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "zappingCount": 1, "zappingTime": 1,' + '"testCount":{"program":' + str(program) + ',"vod":' + str(vod) + ',"ott":' + str(ott) + '}}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "zappingCount": 1, "zappingTime": 1, "testCount": {"program": program, "vod": vod, "ott": ott}}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False
    print('  > You might see the nudge after changing any channel and watching the channel for 10 seconds')
    return True

def setTestCountAiChannel():
    program = 3
    vod = 3
    ott = 1
    try :
        program = int(input(' >> input program count (default {}) : '.format(program)))
        vod = int(input('\n >> input vod count (default {}) : '.format(vod)))
        ott = int(input('\n >> input ott count (default {}) : '.format(ott)))
    except:
        program = 3
        vod = 3
        ott = 1
        print('\nset default count of program, vod, ott : 3, 3, 1')
    return program, vod, ott

def nu_watch_tv_end_1():
    nu_tv_on_complete()
    insertHistory("nu_watch_tv_live_ott", time.localtime(), "SELECTED",  "TERMINATED", day=-28 )
    insertHistory("nu_watch_tv_end_1", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    print(" -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": true, "testType":["nu_watch_tv_end_1"]}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": True, "testType":["nu_watch_tv_end_1"]}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False
    print('  > You might see the nudge after watching a channel which has program information for 10 seconds')
    return True

def nu_AI_channel():
    nu_tv_on_complete()
    insertHistory("nu_watch_tv_live_ott", time.localtime(), "SELECTED",  "TERMINATED", day=-28 )
    insertHistory("nu_AI_channel", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    program, vod, ott = setTestCountAiChannel()
    print("\n -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": true, "testType":["nu_AI_channel"],' + '"testCount":{"program":' + str(program) + ',"vod":' + str(vod) + ',"ott":' + str(ott) + '}}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": True, "testType":["nu_AI_channel"], "testCount": {"program": program, "vod": vod, "ott": ott}}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    if bRet == False : return False
    print('  > You might see the nudge after watching a channel which has program information for 10 seconds')
    return True

def nu_watch_tv_live_ott():
    nu_tv_on_complete()
    insertHistory("nu_watch_tv_live_ott", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    print(" -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": true, "testType":["nu_watch_tv_live_ott"]}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": True, "testType":["nu_watch_tv_live_ott"]}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('  > You might see the nudge after watching a channel which has program information for 10 seconds')
    if bRet == False : return False
    return True

def nu_sport_alarm():
    nu_tv_on_complete()
    insertHistory("nu_sport_alarm", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    print(" -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": true, "testType":["nu_sport_alarm"]}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": True, "testType":["nu_sport_alarm"]}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('  > You might see the nudge after watching a channel which has program information for 10 seconds')
    if bRet == False : return False
    return True

def nu_AI_channel_on():
    nu_tv_on_complete()
    insertHistory("nu_AI_channel_on", time.localtime(), "SELECTED",  "READY", day=-29 )
    reloadHistoryDB()
    bRet, appId = getForegorundApp()
    if bRet == False : return bRet
    if checkInputcommonAppId(appId) == False: return False
    print(" -----------------------------------------")
    print(' # luna-send -n 1 -f luna://com.webos.applicationManager/launch \'{ "id":"' + appId + '", "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": true, "testType":["nu_AI_channel_on"]}}\' ')
    print('  > automatic : ', bAutomatic)

    api = 'luna://com.webos.applicationManager/launch'
    payload = { "id":appId, "params": {"id": "testNudge", "programWatchCheckTime": 0.1, "programEndCheckTime": 1, "modifyEndTime": True, "testType":["nu_AI_channel_on"]}}
    ret = lunaCommand( api, payload )
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj,'returnValue',True)
    print('  > you might see the nudge after watching a channel which has program information for 10 seconds')
    if bRet == False : return False
    return True

def generateStringCondtion():
    #nu_start(True)           # ok
    #nu_tv_on_3(True)           # ok
    #nu_tv_on_magic(True)       # ok
    #nu_tv_on_1(True)           # ok
    #nu_app_entry('com.webos.app.browser', True)    # ok
    #nu_amazon_entry(True)       # killall nudge, # ok
    nu_setting_on(True)       # killall nudge, # ok
    return False

    #nu_setting_off(True)           # ok
    #nu_setting_on(True)            # test
    #return True

def checkString(nudgeId = 'common'):
    i = 0
    prevPath = "/tmp/nudgeString/capture/"+nudgeId+"/"
    delCmd = "rm "+prevPath+"*"
    os.system( delCmd )
    os.system( "/tmp")
    os.system( "/tmp/nudgeString")
    os.system( "/tmp/nudgeString/capture")
    os.system( "/tmp/nudgeString/capture/"+nudgeId)


    for loc in localeLists:
        i=i+1
        print("\n")
        print("INDEX : %d - LOCATION : %s" % (i, loc))

        changeLocale(loc)
        checkToast = generateStringCondtion()
        time.sleep(2)

        path = prevPath+nudgeId+"_"+loc+".jpg"
        #print(path)
        captureScreen(path)
        time.sleep(2)
        if checkToast == True :
            enterKey("ENTER")
            time.sleep(2)
            path = prevPath+nudgeId+"_toast_"+loc+".jpg"
            captureScreen(path)
            time.sleep(2)
            enterKey("EXIT")
            time.sleep(1)
        else :
            enterKey("EXIT")
            time.sleep(1)

    return True

def nu_channel_manager():
    nu_tv_on_complete()

    print('\n')
    print('\n')
    print('\n')
    print('ADD IP CHANNEL')
    lst = getChannelList("IP")
    fillUCMLog( UCM_LIVE_KIND, lst, usingTime = 5*60*60, margineTime=30*60)
    reloadUCMDB()
    print(" -----------------------------------------")
    print(' * Try edit favorite channel on [setting]-[channelManager]')
    return True

def nu_live_menu():
    nu_tv_on_complete()

    print('\n')
    print('\n')
    print('\n')
    print('ADD IP CHANNEL')
    lst = getChannelList("IP")
    fillUCMLog( UCM_LIVE_KIND, lst, usingTime = 5*60*60, margineTime=30*60)
    insertHistory("nu_live_menu", time.localtime(), "SELECTED","TERMINATED", day=-20 )
    reloadUCMDB()
    print(" -----------------------------------------")
    print(' * Try livemenu')
    return True

def nu_airplay():
    clearUCMDB( UCM_APP_KIND)
    clearUCMDB( UCM_LIVE_KIND)
    clearUCMDB( UCM_STB_KIND)
    reloadUCMDB()

    clearHistoryDB()
    insertHistory("nu_setting_on", time.localtime(), "CLOSED",  "TERMINATED", day=-22 )
    insertHistory("nu_start", time.localtime(), "TIMEOUT", "TERMINATED", day=-21 )
    insertHistory("nu_tv_on_3", time.localtime(), "SELECTED","TERMINATED", day=-20 )
    insertHistory("nu_tv_on_magic", time.localtime(), "CLOSED",  "TERMINATED", day=-19 )
    insertHistory("nu_tv_on_1_6item", time.localtime(), "CLOSED",  "TERMINATED", day=-18 )
    insertHistory("nu_tv_on_1", time.localtime(), "CLOSED",  "TERMINATED", day=-17 )
    insertHistory("nu_airplay", time.localtime(), "TIMEOUT", "READY", day=-10 )

    reloadHistoryDB()
    displayHistoryDB(None)
    print(" -----------------------------------------")
    print(" * Please reset tv power")

    if bAutomatic : resetGlobalNudgeEmitter()
    return True


def nu_homekit():
    nu_tv_on_complete()

    api = "luna://com.webos.service.nudge/requestNudge"
    payload = {
        "nudgeId": "nu_homekit",
        "items": [{
            "message": "Do you want to try HomeKit to control TV with iPhone?",
            "button": "OK",
            "responseParams": {
                "onClickAction": {
                    "api": "luna://airplay.service/showHomekitSettingPage",
                    "params": {}
                }
            },
            "type": "Text"
        }]
    }
    lunaCommand( api, payload)
    return True

def nu_livepick(initLog = True):
    if initLog == True :
        nu_tv_on_complete(pushUCMLog = False)

    api = "luna://com.webos.service.nudge/requestNudge"
    payload = {
        "nudgeId": "nu_livepick",
        "items": [{
            "message": "TEST nu_livepick",
            "button": "YES",
            "responseParams": {
                "onClickAction": {
                    "api": "luna://com.webos.notification/createToast",
                    "params": {
                        "message": "nu_livepick selected"
                    }
                }
            },
            "type": "Text"
        }]
    }
    lunaCommand( api, payload)
    return True

def nu_instance(initLog = True):
    if initLog == True :
        nu_tv_on_complete(pushUCMLog = False)

    api = "luna://com.webos.service.nudge/requestNudge"
    payload = {
        "nudgeId": "nu_instance",
        "items": [{
            "message": "TEST nu_instance",
            "button": "YES",
            "responseParams": {
                "onClickAction": {
                    "api": "luna://com.webos.notification/createToast",
                    "params": {
                        "message": "nu_instance selected"
                    }
                }
            },
            "type": "Text"
        }]
    }
    lunaCommand( api, payload)
    return True

def test1():
    clearHistoryDB()
    generateUCMBase()
    reloadHistoryDB()

    insertHistory("nu_setting_on",              time.localtime(), "SELECTED", "TERMINATED", day=-30);
    insertHistory("nu_start",                   time.localtime(), "CLOSED",   "TERMINATED", day=-29 );
    insertHistory("nu_tv_on_magic",             time.localtime(), "SELECTED", "TERMINATED", day=-28 );
    insertHistory("nu_airplay",                 time.localtime(), "SELECTED", "TERMINATED", day=-27 );
    insertHistory("nu_tv_on_livepick",          time.localtime(), "SELECTED", "TERMINATED", day=-26 )
    insertHistory("nu_tv_on_BT_surround",       time.localtime(), "SELECTED", "TERMINATED", day=-25 )
    insertHistory("nu_tv_on_1_6item",           time.localtime(), "TIMEOUT", "READY", day=-24);
    insertHistory("nu_tv_on_1",                 time.localtime(), "TIMEOUT", "READY", day=-23);
    insertHistory("nu_watch_tv_end_1",          time.localtime(), "TIMEOUT", "READY", day=-22);

    #1 - #29
    for i in range(29):
        insertHistory("nu_tv_on_1",                 time.localtime(), "CLOSED", "READY", day=-10, hour=-i )

    reloadHistoryDB()

def test2():
    clearHistoryDB()
    insertHistory("nu_setting_on",              1546300830, "SELECTED", "TERMINATED");
    insertHistory("nu_start",                   1553812849, "CLOSED",   "TERMINATED" );
    insertHistory("nu_tv_on_magic",             1553831678, "SELECTED", "TERMINATED" );
    insertHistory("nu_airplay",                 1553831778, "SELECTED", "TERMINATED" );
    insertHistory("nu_tv_on_1_6item",           1556232965, "TIMEOUT", "READY");
    insertHistory("nu_tv_on_1",                 1556232965, "TIMEOUT", "READY");
    insertHistory("nu_watch_tv_end_1",          1556246896, "TIMEOUT", "READY");

    insertHistory("nu_tv_on_1",                 1562130240, "CLOSED", "SUSPENDED");
    insertHistory("nu_tv_on_1",                 1562130340, "SELECTED", "READY" );
    insertHistory("nu_tv_on_1",                 1562130343, "SELECTED", "READY" );
    insertHistory("nu_tv_on_1",                 1562130348, "SELECTED", "READY" );
    insertHistory("nu_tv_on_1",                 1562130440, "CLOSED", "SUSPENDED");
    insertHistory("nu_tv_on_1",                 1562130540, "SELECTED", "READY" );

    reloadHistoryDB()

#==============================================================================

def dispMenu():
    print('''
------------------------------------------------
Test :
    test-cc.    unit test for caseConditions
    test-1r1d.  unit test for 1 recommend for a day
    test-home.  unit test for tv on nudges (homeAutoLaunch off -> display)

HistoryDB :
    00. reload for Nudge
    01. display
    02. clear

UCM DB:
    10. reload for UCM
    11. display All
    12. display App
    13. display Channel(LiveTV)
    14. display Channel(STB)
    15. clear All
    16. clear App
    17. clear Channel(LiveTV)
    18. clear Channel(STB)

Nudge :
    21. reset nudge service
    22. put default UCM logs
    23. nudge test init
    24. show globalNudge state(pmLog)
    25. get nudge state
    26. set nudge state
    27. generate dummyServerConfiguration(block server desc)
    28. homeAutoLaunch off

Make TestCondition :
    31. nu_start
    32. nu_tv_on_3
    33. nu_tv_on_magic
    34. nu_tv_on_1_6item
    35. nu_tv_on_1

    41. nu_amazon_entry
    42. nu_app_entry
    43. [SPEC-OUT] nu_voice_entry
    46. nu_setting_off
    47. nu_setting_on

    51. nu_ch_watch_tv_n_times
    52. nu_ch_zapping
    53. nu_watch_tv_end_1
    54. nu_watch_tv_live_ott
    55. nu_channel_manager
    56. nu_sport_alarm
    57. nu_AI_channel_zapping
    58. nu_AI_channel
    59. nu_AI_channel_on
    60. nu_live_menu
------------------------------------------------
    ''')
    return

#--< test >--


#--< main >--
argc = len(sys.argv)
argv = sys.argv

dictArg = {}
ret, currAccount = getLoginId()

dispMenu()
while True:
    cmd = input('\n> Input command : ')

    if len(cmd) == 0:
        dispMenu()
        continue

    token = cmd.split(':')
    if len(token) == 2:
        dictArg[token[0]] = token[1]
        print('[INFO] Set argument %s : %s' % (token[0], token[1]))
        continue
    if cmd == 'auto' :
        bAutomatic = not bAutomatic
        print(' Auto MODE : ', bAutomatic)
        continue
    if cmd == '00' :        reloadHistoryDB()
    elif cmd == '01' :      displayHistoryDB()
    elif cmd == '02' :      clearHistoryDB()

    elif cmd == '10' :      reloadUCMDB()
    elif cmd == '11' :
        displayUCMDB(UCM_APP_KIND, detail = False)
        displayUCMDB(UCM_LIVE_KIND, detail = False)
        displayUCMDB(UCM_STB_KIND, detail = False)
    elif cmd == '12' :       displayUCMDB(UCM_APP_KIND )
    elif cmd == '13' :       displayUCMDB(UCM_LIVE_KIND )
    elif cmd == '14' :       displayUCMDB(UCM_STB_KIND )
    elif cmd == '15' :
        clearUCMDB( UCM_APP_KIND)
        clearUCMDB( UCM_LIVE_KIND)
        clearUCMDB( UCM_STB_KIND)
    elif cmd == '16' :      clearUCMDB( UCM_APP_KIND)
    elif cmd == '17' :      clearUCMDB( UCM_LIVE_KIND)
    elif cmd == '18' :      clearUCMDB( UCM_STB_KIND)

    elif cmd == '21' :      resetGlobalNudgeEmitter()
    elif cmd == '22' :      generateUCMBase()
    elif cmd == '23' :      nu_tv_on_1()
    elif cmd == '24' :      displayGlobalNudgeState()
    elif cmd == '25' :      displayNudgeState()
    elif cmd == '26' :      setNudgeState()
    elif cmd == '27' :      generateDummyServerConfiguration()
    elif cmd == '28' :      setSettings( 'general', 'homeAutoLaunch', 'off')

    elif cmd == '31' :      nu_start()
    elif cmd == '32' :      nu_tv_on_3()
    elif cmd == '33' :      nu_tv_on_magic()
    elif cmd == '34' :      nu_tv_on_1_6item()
    elif cmd == '35' :      nu_tv_on_1()
    elif cmd == '35+' :
        n=1
        while True:
            print('[INFO] %dth try' % n)
            nu_tv_on_1()
            time.sleep(12)
            n=n+1

    elif cmd == '41' :      nu_amazon_entry()       # need to UCM DB
    elif cmd == '42' :
        appId = 'com.webos.app.browser'
        if "appId" in dictArg:
            appId = dictArg['appId']
        print('[INFO] Test for AppId(%s)' % appId)
        nu_app_entry(appId)     # need to UCM DB

    elif cmd == '43' :
        nu_voice_entry()        # need to UCM DB
    elif cmd == '46' :
        nu_setting_off()
    elif cmd == '47' :
        nu_setting_on()

    elif cmd == '51' :
        nu_ch_watch_tv_n_times()
    elif cmd == '52' :
        nu_ch_zapping()
    elif cmd == '53' :
        nu_watch_tv_end_1()
    elif cmd == '54' :
        nu_watch_tv_live_ott()
    elif cmd == '55' :
        nu_channel_manager()
    elif cmd == '56' :
        nu_sport_alarm()
    elif cmd == '57' :
        nu_AI_channel_zapping()
    elif cmd == '58' :
        nu_AI_channel()
    elif cmd == '59' :
        nu_AI_channel_on()
    elif cmd == '60' :
        nu_live_menu()
    elif cmd == 'airplay' :
        nu_airplay()
    elif cmd == 'homekit' :
        nu_homekit()
    elif cmd == 'locale':
        checkString()
    elif cmd == 'tv_on_livepick':
        nu_tv_on_livepick()
    elif cmd == 'tv_on_BT_surround':
        nu_tv_on_BT_surround()
    elif cmd == 'livepick' :
        nu_livepick()
    elif cmd == 'instance' :
        nu_instance()

    elif cmd == 'cc-t' or cmd == 'test-cc':
        unitTest4CaseCondition()
    elif cmd == 'test-1r1d':
        unitTest4Recommend1DayGroup()
    elif cmd == 'test-home':
        unitTest4HomeLaunchforTVOnNudge()
    elif cmd == 'server-test' :
        os.system("mkdir /mnt/lg/cmn_data/nudge/");
        os.system("touch /mnt/lg/cmn_data/nudge/serverTestMode.json");
        os.system('kill -9 $(pgrep nudge)')

    elif cmd == 't1':
        test1()
    elif cmd == 't2':
        test2()

    elif cmd == 'reset':
        os.system('kill -9 $(pgrep nudge)')
    else :
        print('[WARN] Undefined command : ', cmd)
