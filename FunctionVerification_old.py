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
    var/palm/license/eulaInfoNetwork.json, 전체동의 약관구조를 참조, "eulaGroupName":"all", "mandatory":[~] 참조
    '''
    cmd = 'cat ../../../../../var/palm/license/eulaInfoNetwork.json'
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
    # print(f'Country setting : {Country_code}')    
    return Country_code

def GetqcardTitle() :
    qCardTitlelist = []
    api = 'luna://com.webos.service.homelaunchpoints/listQcards'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, qcardlist = jsonGetKeyValue(retObj, 'launchPointes')
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
    time.sleep(5)
    
    return True
    
def EulaTest(ServerIndex) :
    print('> -- start Eula Test -- <')
    
    DBcountry = ['KR']
    
    for objCountry in DBcountry :
        if ServerIndex == 'Production' :
            SetCountry(objCountry)
            DeviceData = MakeData()
            ServerData = GetEulaSettingsinDB()
            
            if DeviceData['country_code'] in ServerData.keys() :
                code = DeviceData['country_code']
                if DeviceData['terms_code'] == ServerData[code]['terms_code'] :
                    print('> ------------------------------------------------- <')
                    print(f'country_code : {code}')
                    print(f'terms_code : {DeviceData["terms_code"]}')
                    print('> -- Reulst : Success -- < ')
                else :
                    print('> ------------------------------------------------- <')
                    print('> -- Warning : Please check the Server Eula Data -- <')
                    
            else :
                print('> -- Warning : Please check the country code -- <')                

        elif ServerIndex != 'Production' :
            print()
            print('> -- Server Index : {} -- <'.format(ServerIndex))
            print('> -- Warning : Please Change the ServerIndex')
    return
        
def QcardTest() :
    DeviceData = MakeData()
    ServerData = GetQcardSettingsinDB()
    
    if DeviceData['country_code'] in ServerData.keys() :
        print('> -- start Q-card Test -- <')
        code = DeviceData['country_code']
        if sorted(ServerData[code]['Q-Card Title']) == sorted(DeviceData['Q-card Title']) :
            print('> ------------------------------------------------- <')
            print(f'country_code : {code}')
            print(f'Q-card List : {DeviceData["Q-card Title"]}')
            print('> -- Reulst : Success -- < ')
        else :
            print('> ------------------------------------------------- <')
            print('> -- Warning : Please check the Server Q-card Data -- <')
    else :
        print('> -- Please Check the country/Server Data')
        
    return

# <-- disp Test Menu --> #
            
def dispMenu() :
    print('''
------------------------------------------------
TestCondition :
    00. Server condition
    01. Server Change

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
        
        elif cmd == '10' :  EulaTest(ServerIndex)
        elif cmd == '11' :  QcardTest()
        
        