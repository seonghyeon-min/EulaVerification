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
    
def OpenJsonFile(file) :
    with open(file, 'r') as file :
        data = json.loads(file.read())
        
    return data
    
def MergeData() :
    JsonList = ['eula.json', 'qcard.json', 'hotkey.json']
    basedata = {}
    
    for json in JsonList :
        data = OpenJsonFile(json)
        for cntrycode, value in data.items() :
            if cntrycode in basedata.keys() :
                for key in data[cntrycode].keys() :
                    if key.lower() not in basedata[cntrycode].keys() :
                        basedata[cntrycode][key] = data[cntrycode][key]
            else:
                basedata[cntrycode] = value
    
    return basedata                
    

def GetServerParam() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/getServer '{}'
    {
        "returnValue": true,
        "serverIndex": "Production"
    }
    '''
    api = 'luna://com.webos.service.sdx/getServer'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, serverIndex = jsonGetKeyValue(retObj, 'serverIndex')
    if bRet == False : return 0
    param = serverIndex
    
    print(f"> -- SERVER : {param} -- <")
    return param

def SetServerParam(serverIndex) :
    print()
    print('> -- Start ServerSetting... -- <')
    print('Current ServerIndex : ', serverIndex)
    while True :
        if serverIndex == 'Production' :
            print(f'> -- SERVER : {serverIndex} -- <')
            break
        else :
            api = 'luna://com.webos.service.sdx/setServer'
            payload = {"serverIndex":"Production"}
            ret = lunaCommand(api, payload)
            retObj = json.loads(ret)
            bRet, returnValue = jsonGetKeyValue(retObj, 'reternValue')
            if not returnValue : return 0 
            print(f'> -- MODIFICATION OF SERVER : SUCCESS -- <')
    return True

def GetEulaSettingsinDevice() :
    '''
    var/palm/license/eulaInfoNetwork.json, 전체동의 약관구조를 참조, 
    {"eulaGroupName":"all", "mandatory":[..]}
    '''
    cmd = 'cat ../../../../../var/palm/license/eulaInfoNetwork.json'
    try :
        eulaData = json.loads(runSystem(cmd))    
    except :
        # load Eula
        print('[WARN] EUlA needs to be loaded ')
        api = 'palm://com.webos.applicationManager/launch'
        payload = {"id":"com.webos.app.firstuse-overlay", 
                   "params":{"target":"eula", "context":"eulaUpdate"}}
        ret = lunaCommand(api, payload)
        time.sleep(5)
        retObj = json.loads(ret)
        bRet = jsonCheckKeyValue(retObj, 'returnValue', True)
        if bRet == False : return False, None
        eulaData = json.loads(runSystem(cmd))        
    
    for data in eulaData['eulaMappingList']['eulaInfo'] :
        if data['eulaGroupName'] == 'all':
            eulalist = data['mandatory'] # 스마트모니터 약관 구조
    return list(eulalist)

def GetCountryInfo() :
    api = 'luna://com.webos.service.sdx/getHttpHeaderForServiceRequest'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, CountryCode = jsonGetKeyValue(retObj, 'X-Device-Country')
    if bRet == False : return 0
    Country_code = CountryCode
    print(f'> -- Country setting : {Country_code} -- <')    
    return Country_code

def GetqcardTitle() :
    qCardTitlelist = []
    api = 'luna://com.webos.service.homelaunchpoints/listQCards'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, qcardlist = jsonGetKeyValue(retObj, 'launchPoints')
    if bRet == False : return 0
    for qcard in qcardlist :
        qCardTitlelist.append(qcard['title'])
        
    return qCardTitlelist

def GetHKSetting() :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send '{"serviceName":"service
    _setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD", "bodyData
    ":"{\"requester\":\"hot_key\"}", "contentType":"application/json"}'
    '''
    HotKeySettingData = defaultdict(list)
    HotkeySettingDict = defaultdict(list)
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure",
               "url":"getConfig",
               "methodType":"REQ_SSL_POST_METHOD", 
               "bodyData":"{\"requester\":\"hot_key\"}", "contentType":"application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, HotKeyData = jsonGetKeyValue(retObj, 'serverResponse') 
    if bRet == False : return 0
    resp = json.loads(HotKeyData['response'])['mapping_info']
    
    for app in resp :
        for title, param in app.items() :
            for key, value in param.items() :
                if key == 'launch_param' : pass
                else :
                    HotKeySettingData[title].append((key, value))
                    
    for item in HotKeySettingData :
        dictmp = dict()
        for k, v in HotKeySettingData[item] : 
            dictmp[k] = v
        HotkeySettingDict[item].append(dictmp)
    
    return HotkeySettingDict
    
    
def MakeData() :
    Country_code = GetCountryInfo()
    terms_code = GetEulaSettingsinDevice()
    qCardTitle = GetqcardTitle()
    hotkeySetting = GetHKSetting()
    
    object_db = {
        'country_code' : Country_code,
        'terms_code' : terms_code,
        'Q-Card Title' : qCardTitle,
        'HotKey' : hotkeySetting,
    }
    
    print()
    print('> ------------------ Device Data ------------------ <')
    print(json.dumps(object_db, indent=4))
    print('> ------------------------------------------------- <')
    return object_db

def GetEulaSettingsinDB() :
    with open('eula.json', 'r') as file :
        eula_db = json.loads(file.read())
    return eula_db

def GetQcardSettingsinDB() :
    with open('qcard.json', 'r') as file :
        qCard_db = json.loads(file.read())
    return qCard_db

def GetHKSettingsinDB() :
    with open('hotkey.json', 'r') as file :
        hk_db = json.loads(file.read())
    return hk_db

def SetCountry(objCountry) :
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/setCountrySettingByManual '{"code2" : "NZ","code3" : "NZL", "type" : "smart"}'
    '''
    EulaDB = GetEulaSettingsinDB()
    api = 'luna://com.webos.service.sdx/setCountrySettingByManual'
    payload = {"code2" : objCountry, "code3" : EulaDB[objCountry]['country_three_code'], "type" : "smart"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, returnValue = jsonGetKeyValue(retObj, 'returnValue')
    if bRet == False : return 0
    if returnValue == False :
        print('> -- Fail to change the country, please check the server status -- <')
    print(f'> -- Country : {GetCountryInfo()} -- <')
    time.sleep(10)
    
    return True

def EulaTest(DeviceData, CntryCode) :
    ServerData = GetEulaSettingsinDB()
    code = CntryCode
    result = dict()
    
    if DeviceData['country_code'] in ServerData.keys() :
        print('> -- start Eula Test -- <')
        time.sleep(3)
        if DeviceData['terms_code'] == ServerData[code]['terms_code'] :
            print(' > --------------------------------------------------- < ')
            result = {'returnValue' : {'Result' : True, 'CountryCode' : code, 'termsCode' : DeviceData['terms_code']}}
            print(json.dumps(result, indent=4))      

        else :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : False, 
                                        'CountryCode' : code, 
                                        'messages' : '[WARN] : Check EulaData/Loading Status.'}}
            print(json.dumps(result, indent=4))
        
    else :
        print('> -- Warning : Please check the country code -- <')           

    return result
        
def QcardTest(DeviceData, CntryCode) :
    ServerData = GetQcardSettingsinDB()
    code = CntryCode
    result = dict()
    
    if DeviceData['country_code'] in ServerData.keys() :
        print('> -- start Q-card Test -- <')
        time.sleep(3)
        if sorted(ServerData[code]['Q-Card Title']) == sorted(DeviceData['Q-Card Title']) :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : True, 
                                        'CountryCode' : code, 
                                        'qCardList' : DeviceData['Q-Card Title']}}
            print(json.dumps(result, indent=4))
            
        else :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : False, 
                                        'CountryCode' : code, 
                                        'messages' : '[WARN] : Check Q-Card Server Data.'}}
            print(json.dumps(result, indent=4))
    else :
        print('> -- Please Check the country/Server Data')
        
    return result

def HotKeyTest(DeviceData, CntryCode):
    ServerData = GetHKSettingsinDB()
    code = CntryCode
    flag = 'N'
    result = dict() 
    
    if DeviceData['country_code'] in ServerData.keys() :
        print('> -- start Hot Key Test -- <')
        time.sleep(3)
        param = ServerData[code]['HotKey']
        for key in param : 
            status, Id = DeviceData['HotKey'][key][0].values()
            status = str(status)
            if (param[key][0]['app_id'] == Id) and (param[key][0]['isActive'] == status) :
                flag = 'Y'
            else :
                flag = 'N'
                

        if flag == 'Y' : 
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : True, 
                                    'CountryCode' : code, 
                                    'qCardList' : DeviceData['HotKey']}}
            print(json.dumps(result, indent=4))
        
        else :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : False, 
                                    'CountryCode' : code, 
                                    'qCardList' : DeviceData['HotKey']}}
            print(json.dumps(result, indent=4))
            
    else :
        print('> -- Please Check the country/Server Data')
        

def MagicLinkTest() :  # supportedByTipsServer -> True or False ? 
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send 
    '{"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD", 
    "ric" : "KIC", "bodyData":"{\"requester\":\"nlp\"}", "contentType" : "application/json"}'
    '''
    
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure",
                "url":"getConfig","methodType":"REQ_SSL_POST_METHOD", 
                "ric" : "KIC", "bodyData":"{\"requester\":\"nlp\"}",
                "contentType" : "application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, MagicLinkData = jsonGetKeyValue(retObj, 'serverResponse')
    if bRet == False : return 0 
    res = json.loads(MagicLinkData['response'])
    result = {}

    '''
    magicLink : {'orderedCategory': ['youtube', 'genre', 'web', 'person', 'ost'], 'defaultCategory': 'youtube', 'supportedByTipsServer': True, 'ipChannelSupported': True, 'switch': True}
    '''
    
    if 'magicLink' in res.keys() :
        if res['magicLink']['supportedByTipsServer'] == True :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : True,
                                    'supportedByTipsServer' : res['magicLink']['supportedByTipsServer'] } }
            print(json.dumps(result, indent=4))
            
        else :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : False,
                                    'supportedByTipsServer' : res['magicLink']['supportedByTipsServer'] } }
            print(json.dumps(result, indent=4))
        
    else :
        print('> -- Please Check \'magicLink\' Key is in Server -- <')

def EPGTest() : # tuner_ch_map -> false, tuner_epg -> false because tuner isn't supported 
    '''
    luna-send -n 1 -f luna://com.webos.service.sdx/send '{"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD","bodyData":{"requester" : "epg"}, "contentType" : "application/json"}'
    '''
    
    api = 'luna://com.webos.service.sdx/send'
    payload = {"serviceName":"service_setting_secure","url":"getConfig","methodType":"REQ_SSL_POST_METHOD","bodyData":{"requester" : "epg"}, "contentType" : "application/json"}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, epgData = jsonGetKeyValue(retObj, 'serverResponse')
    if bRet == False : return 0
    res = json.loads(epgData['response'])['epg_info']
    flag = 'N'
    
    tuner_result = {}
    result = {}
    
    for epgInfo in res :
        if (epgInfo['id'] == 'tuner_ch_map') or (epgInfo['id'] == 'tuner_epg') :
            if epgInfo['isActive'] == False :
                tuner_result[epgInfo['id']] = epgInfo['isActive']
                flag = 'Y'
            else :
                tuner_result[epgInfo['id']] = epgInfo['isActive']
                flag = 'N'
            
        elif ('tuner_ch_map' not in epgInfo.keys()) or ('tuner_epg' not in epgInfo.keys()) :
            flag = 'N' 
    
    
    if flag == 'Y' :
        result = {'returnValue' : {
                                'Result' : True,
                                'epgInfo' : tuner_result
                                } 
                }
    else :
        result = {'returnValue' : {
                                'Result' : False,
                                'epgInfo' : tuner_result
                                } 
                }

    print(json.dumps(result, indent=4))

# ======================================================================================================= #
def TestConfing() :
    TestFunc = {}
    Database = MergeData()                      # type : dict
    CntryCode = GetCountryInfo()                # CountryCode : two_code
    Keylist = list(Database[CntryCode].keys())  # ['country_three_code', 'country_info', 'terms_code', 'Q-card Title'...]
    StdIdx = Keylist.index('terms_code')
    Funclst= ['Eula', 'qCard', 'HotKey']
    
    for func in Funclst :
        TestFunc[func] = Keylist[StdIdx]
        StdIdx += 1
    
    return TestFunc
    
def AutoMode(DeviceData, CntryCode) :
    ServerDB = MergeData()             # DB
    DeviceDB = DeviceData                # Device
    code = CntryCode                     # Setting Device Country code
    TConfig = TestConfing()
    TestFunc = ['Eula', 'qCard', 'HotKey']
    Testconfig = {}
    '''
    DeviceDB = {
        'country_code' : Country_code,
        'terms_code' : terms_code,
        'Q-Card Title' : qCardTitle,
        'HotKey' : ...
        '
    }
    '''   
    for idx, func in enumerate(TestFunc) :
        if (code in ServerDB.keys()) and (func != 'HotKey') :
            if sorted(DeviceDB[TConfig[func]]) == sorted(ServerDB[code][TConfig[func]]) :
                Testconfig[idx+1] = {
                                'ConfigId' : 'AutoTest',
                                'PreConditionsSettings' : [ServerDB[code]['country_info'], ServerDB[code][TConfig[func]]],
                                'UnitTest' : [
                                    {
                                        'id' : func,
                                        'TestResult' : True,
                                    }
                                ]    
                            }
            else :
                Testconfig[idx+1] = {
                                'ConfigId' : 'AutoTest',
                                'PreConditionsSettings' : [ServerDB[code]['country_info'], ServerDB[code][TConfig[func]]],
                                'UnitTest' : [
                                    {
                                        'id' : func,
                                        'TestResult' : False,
                                    }
                                ]    
                            }
                
        elif (code in ServerDB.keys()) and (func == 'HotKey') :
            for Key in DeviceDB[TConfig[func]].keys() :
                AppId, Status = ServerDB[code][TConfig[func]][Key][0]
                dAppId, dStatus = DeviceDB[TConfig[func]][Key][0]
                dStatus = str(dStatus)
                if (AppId == dAppId) and (Status == dStatus) : 
                    Testconfig[idx+1] = {
                                'ConfigId' : 'AutoTest',
                                'PreConditionsSettings' : [ServerDB[code]['country_info'], ServerDB[code][TConfig[func]]],
                                'UnitTest' : [
                                    {
                                        'id' : func,
                                        'TestResult' : True,
                                    }
                                ]    
                            }
                else :
                    Testconfig[idx+1] = {
                                'ConfigId' : 'AutoTest',
                                'PreConditionsSettings' : [ServerDB[code]['country_info'], ServerDB[code][TConfig[func]]],
                                'UnitTest' : [
                                    {
                                        'id' : func,
                                        'TestResult' : False,
                                    }
                                ]    
                            }
                    

    print(json.dumps(Testconfig, indent=4))
    return Testconfig   

# <-- disp Test Menu --> #
            
def dispMenu() :
    print('''
------------------------------------------------
TestCondition :
    00. Server condition
    01. Server Change          < not supported >
    02. Country condition
    03. DB condition

Mode :
    aa. Auto 

FunctionTest :
    10. Eula
    11. Q-card
    12. Hot-key
    13. MagicLink
    14. EPG
    ''')
    return
            
if __name__ == '__main__' :
    print()
    print()
    dispMenu()
    while True :
        cmd = input('\n> Input command : ')
        
        if len(cmd) == 0 :
            dispMenu()
            continue
        
        if cmd == '00' :    ServerIndex = GetServerParam()
        elif cmd == '01' :  SetServerParam(ServerIndex)
        elif cmd == '02' :  CntryCode = GetCountryInfo()
        elif cmd == '03' :  DeviceData = MakeData()
        
        elif cmd == 'aa' :  AutoMode(DeviceData, CntryCode)
                
        elif cmd == '10' :  EulaTest(DeviceData, CntryCode)
        elif cmd == '11' :  QcardTest(DeviceData, CntryCode)
        elif cmd == '12' :  HotKeyTest(DeviceData, CntryCode)
        elif cmd == '13' :  MagicLinkTest()
        elif cmd == '14' :  EPGTest()
        