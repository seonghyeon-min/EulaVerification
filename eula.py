import os
import json
import time

locationLists = []

def lunaCommand(api, payload) :
    cmd = "luna-send -n 1 -f {} \'{}\'".format(api, payload)
    return os.system(cmd)

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


# 2. 국가 변경
# DB 연동

# 3. 약관 구조 확인
# DB 연동
'''
var/palm/license/eulaInfoNetwork.json 
"eulaGroupName":"all", "mandatory":[~] 참조
'''
def GetEulaSettings() :
    cmd = 'cat var/palm/license/eulaInfoNetwork.json'
    eulaData = json.loads(os.system(cmd))
    for data in eulaData['eulaMappingList']['eulaInfo'] :
        if data['eulaGroupName'] == 'all':
            eulalist = data['mandotory'] # 스마트모니터 약관 구조

    
    
    

