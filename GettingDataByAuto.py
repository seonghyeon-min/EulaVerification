from collections import defaultdict
import os
import json
import time
import subprocess

def runSystem(cmd) :
    out = subprocess.check_output(cmd, shell=True)
    return out

def lunaCommand(api, payload) :
    cmd = "luna-send -n 1 -f {} \'{}\'".format(api, json.dumps(payload))
    return runSystem(cmd)

def jsonGetKeyValue(obj, key) :
    try :
        if key in obj :
            value = obj[key]
            return True, value
        return False, None
    
    except Exception as ex :
        print('Exception : ', ex)
        return False, None
    
def jsonCheckKeyValue(obj, key, value) :
    try : 
        if (key in obj) and (obj[key] == value) :
            return True
        return False
    
    except Exception as ex :
        print('Exception : ', ex)
        return False
    
def GetServerCountryParam() :
    '''
    luna-send -n 1 -f palm://com.webos.service.sdx/getServerUrl '{}'
    '''
    api = 'palm://com.webos.service.sdx/getServerUrl'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet = jsonCheckKeyValue(retObj, 'returnValue', True)
    if bRet == False : return False, None
    bRet, CountryPrefix = jsonGetKeyValue(retObj, 'countryPrefix')
    
    if 'qt2' in CountryPrefix :
        serverIndex, Country = 'QA2', CountryPrefix.split('-')[-1]
    else :
        serverIndex, Country = 'Production', CountryPrefix.split('-')[-1]
            
    return serverIndex, Country

# GetEulaData
def GetEulaData() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send '{"serviceName":"sdp_secure","url":"eulamapping","methodType":"REQ_SSL_GET_METHOD"}'
    '''
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"sdp_secure","url":"eulamapping","methodType":"REQ_SSL_GET_METHOD"}
    ret = lunaCommand(api, payload)
    retObj  = json.loads(ret)
    bRet, ServerResponse = jsonGetKeyValue(retObj, 'serverResponse')
    if bRet == False : return 0
        
    if ServerResponse['code'] == '200' :
        Resp = json.loads(ServerResponse['response'])['eulaMappingList']['eulaInfo']
        for group in Resp :
            if group['eulaGroupName'] == 'all' :
                eula = group['mandatory']
                
    elif ServerResponse['code'] == '204' :
        print('Please Check Server setting Value')
        return 'False'

    print("====================================================================")
    print('> Eula Setting : {}'.format(', '.join(eula)))
    print()
    return eula

# GetQcardData
def GetQcardData() :
    '''
    luna-send -n 1 -f luna://com.webos.service.homelaunchpoints/listQCards '{}'
    '''
    qCardTitleList = []
    api = 'luna://com.webos.service.homelaunchpoints/listQCards'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, qcardlst = jsonGetKeyValue(retObj, 'launchPoints')
    if bRet == False : return 0
    for qcard in qcardlst : 
        qCardTitleList.append(qcard['qCardTitle'])
        
    if qCardTitleList == [] :
        print('Please Check Server setting Value')
        return 'False'
    else :
        print("====================================================================")
        print('> qCard Setting : {}'.format(', '.join(qCardTitleList)))
        print()
        return qCardTitleList

# GetHotKeyData 
def GetHkData() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send '{"serviceName":"service
    _setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD", "bodyData
    ":"{\"requester\":\"hot_key\"}", "contentType":"application/json"}'
    '''
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure",
                "url":"getConfig",
                "methodType":"REQ_SSL_POST_METHOD", 
                "bodyData":"{\"requester\":\"hot_key\"}", "contentType":"application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, HotKeyData = jsonGetKeyValue(retObj, 'serverResponse')
    if bRet == False : return 0
    
    if HotKeyData['code'] == '200' :
        hotkey = json.loads(HotKeyData['response'])['mapping_info']
        print("====================================================================")
        print('> Hotkey Setting : \n{}'.format(hotkey))
        print()
        return hotkey
    else :
        print('Please Check Server setting Value')    
        return 'False'

# GetHomeShelf
def GetHomeShelfData() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send 
    '{"serviceName":"service_setting_secure", "url":"getConfig", "methodType":"REQ_SSL_POST_METHOD", "bodyData":"{\"requester\":\"ai_home\"}","contentType":"application/json"}'
    '''    
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure", "url":"getConfig", "methodType":"REQ_SSL_POST_METHOD", "bodyData":"{\"requester\":\"ai_home\"}","contentType":"application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, homeshelfData = jsonGetKeyValue(retObj, 'serverResponse')
    homeshelf = []
    if bRet == False : return 0
    
    if homeshelfData['code'] == '200' :
        res = json.loads(homeshelfData['response'])['ai_home_info']
        for shelf in res :
            homeshelf.append({'shefRank' : shelf['shelfRank'],
                            'shelfId' : shelf['shelfId']
                            })
    
    else :
        print('Please Check Server setting Value')    
        return 'False'
    
    print("====================================================================")
    print('> HomeShelf Setting : {}'.format(homeshelf))
    print()
    
    return homeshelf
    
# MagicLink
def GetMgLinkData() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send 
    '{"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD", 
    "ric" : "KIC", "bodyData":"{\"requester\":\"nlp\"}", "contentType" : "application/json"}'
    '''
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD", "ric" : "KIC", "bodyData":"{\"requester\":\"nlp\"}", "contentType" : "application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, MagicLinkData = jsonGetKeyValue(retObj, 'serverResponse')
    MagicLink = []
    if bRet == False : return 0 

    if MagicLinkData['code'] == '200' :
        res = json.loads(MagicLinkData['response'])['magicLink']
        MagicLink.append(res)

        
    else :
        print('Please Check Server setting Value')    
        return 'False'

    print("====================================================================")
    print('> MagicLink Setting : {}'.format(MagicLink))
    print()
    
    return MagicLink

# EPG
def GetepgData() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send '{"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD","bodyData":{"requester" : "epg"}, "contentType" : "application/json"}'
    '''

    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD","bodyData":{"requester" : "epg"}, "contentType" : "application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, epgData = jsonGetKeyValue(retObj, 'serverResponse')
    epg = []
    if bRet == False : return 0
    
    if epgData['code'] == '200' :
        res = json.loads(epgData['response'])['epg_info']
    
    else :
        print('Please Check Server setting Value')    
        return 'False'
    
    for idx in range(len(res)) :
        epg.append({'id' : res[idx]['id'], 'isActive' : res[idx]['isActive']})
            
    print("====================================================================")
    print('> EPG Setting : {}'.format(epg))
    print()
    
    return epg

def WriteJsonFile(file, objJson) :
    with open(file, 'w') as WriteFile :
        json.dump(objJson, WriteFile, indent=4)
        
    if os.path.isfile(file) : 
        return True
    else :
        return False

def CliMode() :
    TestLst = ['Eula', 'qCard', 'HotKey', 'HomeShelf', 'MagicLink', 'EPG']
    funcLst = [GetEulaData, GetQcardData, GetHkData, GetHomeShelfData, GetMgLinkData, GetepgData]
    ResultConfig = {}
    sidx, cntr = GetServerCountryParam()
    
    ResultConfig['precondition'] = {
                                    'server' : sidx,
                                    'country' : cntr
    }
    
    ResultConfig['data'] = []
    for idx, func in enumerate(funcLst) :
        res = func()
        ResultConfig['data'].append({
            TestLst[idx] : res
        })
        
    print(json.dumps(ResultConfig, indent=4))
    now = time
    Exist = WriteJsonFile(f'dataResult_{now.strftime("%Y%m%d%H%M%S")}.json', ResultConfig)
    
    if Exist :
        print('TestConfig.json file has been created')        
    else :
        print('[Warn] Check server address / path is existed')
        
if __name__ == '__main__' :
    print()
    print()
    CliMode()

