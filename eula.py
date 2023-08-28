import os
import json
import time
import subprocess

def runSystem(cmd) :
    out = subprocess.check_output(cmd, shell=True)
    return out

def lunaCommand(api, payload) :
    cmd = "luna-send -n 1 -f {} \'{}\'".format(api, payload)
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

# 1. 서버 변경
'''
luna-send -n 1 -f luna://com.webos.service.sdx/getServer '{}'
{
    "returnValue": true,
    "serverIndex": "Production"
}
'''
def GetServerParam() :
    api = 'luna://com.webos.service.sdx/getServer'
    payload = {}
    ret = lunaCommand(api, payload)
    retObj = json.loads(ret)
    bRet, serverIndex = jsonGetKeyValue(retObj, 'serverIndex')
    if bRet == False : return 0
    param = serverIndex
    print(f'Server : {param}')
    
    return param

def SetServerParam() : 
    while True :
        param = GetServerParam()
        if param == 'Production' :
            print('> MODIFICATION OF SERVER : SUCCESS')
            break
        elif not param == 'Production' :
            api = 'luna-send -n 1 -f luna://com.webos.service.sdx/setServer'
            payload = {"serverIndex":"Production"}
            lunaCommand(api, payload)
            time.sleep(1000)
    return True

# 2. device/DB 내 국가별 약관 구조 확인
# 2.1 Device 내 약관 tree
'''
var/palm/license/eulaInfoNetwork.json 
"eulaGroupName":"all", "mandatory":[~] 참조
'''
def GetEulaSettingsinDevice() :
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
    print(f'Country setting : {Country_code}')    
    return Country_code
    
def MakeDataFrame() :
    Country_code = GetCountryInfo()
    terms_code = GetEulaSettingsinDevice()
    
    object_db = {
        'country_code' : Country_code,
        'terms_code' : terms_code,
    }

    print(object_db)
    
    return object_db

# 2.2 DB 내 약관 tree
def GetEulaSettingsinDB() :
    with open('eula.json', 'r') as file :
        eula_db = json.loads(file.read())
        
    # eula_db = {
    #     'country_code' : 'KR',
    #     'terms_code' : ['S_SVC', 'S_PRV', 'S_PRM', 'S_PRC', 'S_PRD', 'S_VDC', 'S_VDD'],
    # }
    
    print(eula_db)

    return eula_db

# 3. test
def EulaTest() :
    # 1) checking the server
    
    if SetServerParam() :
        device_db = MakeDataFrame()
        database_db = GetEulaSettingsinDB()

        print('> -- start Eula Test -- <')
        
        if device_db['country_code'] in database_db.keys() :
            code = device_db['country_code']
            if device_db['terms_code'] == database_db[code]['terms_code'] :
                print('> -- Please refer to below result -- <')
                print(f'country_code : {code}')
                print(f'terms_code : {device_db["terms_code"]}')
                print('> -- Reulst : Success -- < ')              
            else :
                print('> -- Warning : Please check the server Eula settings -- <')
                
        else :
            print('> -- Warning : Please check the country code -- <')
            
    else :
        print('> Please Check the serverIndex (QA2/Production) ')
        
if __name__ == '__main__' :
    print('')
    EulaTest()