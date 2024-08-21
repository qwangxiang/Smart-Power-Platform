import pandas as pd
from iotdb.Session import Session
import datetime

def iotdbconnect(ip:str='202.120.60.3', port:str='6667'):
    '''
    连接到IOTDB数据库
    '''
    ip_ = ip
    port_ = port
    username_ = 'retrieve'
    password_ = '!2#4QwEr'
    session = Session(ip_, port_, username_, password_)
    session.open(False)
    return session

# 自定义异常
class MyException(Exception): pass

def str2timestamp(str_time:str, time_format:str='%Y-%m-%d %H:%M:%S'):
    '''
    将年月日时分秒的数据转化为时间戳，未乘1000
    '''
    dt = datetime.datetime.strptime(str_time, time_format)
    return int(dt.timestamp())

def timestamp2str(timestamp)->str:
    '''
    将时间戳转换为年月日时分秒，未乘1000
    '''
    dt_object = datetime.datetime.fromtimestamp(timestamp)
    formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_time

def ID2Path(ID:str)->tuple:
    '''
    从设备ID查找其对应的索引，索引全表参考DeviceList.xlsx
    '''
    device_list = pd.read_excel('设备档案/DeviceList.xlsx')
    for row in range(device_list.shape[0]):
        if ID in device_list.iloc[row, 0]:
            ID = device_list.iloc[row, 0]
            id_list = ID.split('`')
            return id_list[1],id_list[0][:-1]


def OneDevice_readDataAt(prefixID:str, afterfixID:str, time:str, dataType:str='P')->pd.DataFrame:
    '''
    查询某个设备某个时间点的数据，时间格式: '2024-06-30 00:00:00'，返回数据的时间格式为时间戳，未除1000
    '''
    try:
        iotsession = iotdbconnect()
    except:
        raise MyException('Could not connect to the IOTDB database')
    else:
        Timestamp = str2timestamp(time)*1000
        querystr = 'select last `' + prefixID + '`.'+dataType+' from '+afterfixID+' where Time <= '+str(Timestamp)
        res = iotsession.execute_query_statement(querystr)
        df = res.todf()
        return df
    finally:
        iotsession.close()
        print('数据库查询结束!')

def OneDevice_readDataBetween(prefixID:str, afterfixID:str, start_time:str, end_time:str, dataType:str='P', if_print=True)->pd.DataFrame:
    '''
    查询某个设备某个时间段的数据，时间格式: '2024-06-30 00:00:00'。返回数据的时间格式为时间戳，未除1000
    '''
    try:
        iotsession = iotdbconnect()
    except:
        raise MyException('Could not connect to the IOTDB database')
    else:
        start_Timestamp = str2timestamp(start_time)*1000
        end_Timestamp = str2timestamp(end_time)*1000
        querystr = 'select `' + prefixID + '`.'+dataType+' from '+afterfixID+' where Time > '+str(start_Timestamp)+' and Time < '+str(end_Timestamp)
        res = iotsession.execute_query_statement(querystr)
        df = res.todf()
        return df
    finally:
        iotsession.close()
        if if_print:
            print('数据库查询结束!')

if __name__=='__main__':
    # 测试
    df = OneDevice_readDataBetween(*ID2Path('Mt1-M1-84f70311392c'), '2024-06-30 00:00:00', '2024-06-30 23:59:59')
    print(df)