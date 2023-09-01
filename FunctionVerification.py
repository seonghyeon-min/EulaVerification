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
    JsonList = ['eula.json', 'qcard.json']
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

def MakeData() :
    Country_code = GetCountryInfo()
    terms_code = GetEulaSettingsinDevice()
    qCardTitle = GetqcardTitle()
    
    object_db = {
        'country_code' : Country_code,
        'terms_code' : terms_code,
        'Q-Card Title' : qCardTitle,
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
        if sorted(ServerData[code]['Q-Card Title']) == sorted(DeviceData['Q-Card Title']) :
            print('> ------------------------------------------------- <')
            result = {'returnValue' : {'Result' : True, 'CountryCode' : code, 'qCardList' : DeviceData['Q-Card Title']}}
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

def TestConfing() :
    TestFunc = {}
    Database = MergeData()                # type : dict
    CntryCode = GetCountryInfo()          # CountryCode : two_code
    Keylist = list(Database[CntryCode].keys())  # ['country_three_code', 'country_info', 'terms_code', 'Q-card Title'...]
    StdIdx = Keylist.index('terms_code')
    Funclst= ['Eula', 'qCard']
    
    for func in Funclst :
        TestFunc[func] = Keylist[StdIdx]
        StdIdx += 1
    
    return TestFunc
    
def AutoMode(DeviceData, CntryCode) :
    DatabaseDB = MergeData()             # DB
    DeviceDB = DeviceData                # Device
    code = CntryCode                     # Setting Device Country code
    TConfig = TestConfing()
    TestFunc = ['Eula', 'qCard']
    Testconfig = {}
    '''
    DeviceDB = {
        'country_code' : Country_code,
        'terms_code' : terms_code,
        'Q-Card Title' : qCardTitle,
    }
    '''   
    for idx, func in enumerate(TestFunc) : 
        if (code in DatabaseDB.keys()) :
            if sorted(DeviceDB[TConfig[func]]) == sorted(DatabaseDB[code][TConfig[func]]) :
                Testconfig[idx+1] = {
                                'ConfigId' : 'AutoTest',
                                'PreConditionsSettings' : [DatabaseDB[code]['country_info'], DatabaseDB[code][TConfig[func]]],
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
                                'PreConditionsSettings' : [DatabaseDB[code]['country_info'], DatabaseDB[code][TConfig[func]]],
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
    01. Server Change
    02. Country condition
    03. DB condition

Mode :
    aa. Auto 

FunctionTest :
    10. Eula
    11. Q-card
    
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
        
        