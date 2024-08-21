import os
import sys
sys.path.append(os.getcwd())

import pandas as pd
from DataProcess import ReadData
import numpy as np
import streamlit as st

class Device:
    def __init__(self, id:str) -> None:
        self.id = id
        if id!='None':
            df = pd.read_excel('设备档案/电院群楼设备档案.xlsx', sheet_name='电院群楼设备总表')
            df = df[df['设备mac'] == id]
            if df.empty:
                pass
            else:
                df = df.iloc[0,:]
                self.mac,self.name,self.gateway_id,self.gataway_name,self.transform_ratio = tuple(df.fillna('None').to_list())
        else:
            pass
    
    def isNoneDevice(self):
        return self.id=='None'

    def readDataAt(self, time:str, datatype:str='P'):
        '''
        读取设备在某个时间点的数据，时间格式：'2024-06-30 00:00:00'，返回数据时间格式是时间戳，已除1000
        '''
        df = ReadData.OneDevice_readDataAt(*ReadData.ID2Path(self.id), time, datatype)
        if df.empty:
            return df
        else:
            df.iloc[:,0] = df.iloc[:,0]/1000
            return df
        
    def readDataBetween(self, start:str, end:str, datatype:str='P'):
        '''
        读取设备在某个时间段的数据，时间格式：'2024-06-30 00:00:00'，返回数据时间格式是时间戳，已除1000
        '''
        df = ReadData.OneDevice_readDataBetween(*ReadData.ID2Path(self.id), start, end, datatype)
        if df.empty:
            return df
        else:
            df['Time'] = df['Time']/1000
            return df
        
    def show_info(self):
        '''
        展示设备基础信息
        '''
        if self.isNoneDevice():
            print("None Device!")
            return
        print(f" mac: {self.mac}", end='')
        print(f" 设备名称: {self.name}", end='')
        print(f" 网关id: {self.gateway_id}", end='')
        print(f" 网关名称: {self.gataway_name}", end='')
        print(f" 变比: {self.transform_ratio}")

class Room:
    def __init__(self, id:str) -> None:
        df = pd.read_excel('设备档案/Device_Info.xlsx', sheet_name='信息总表')
        df = df[df['房间编号']==id].iloc[0,:]
        if df.empty:
            raise ValueError(f"Room with id {id} not found")
        self.id,self.room_num,self.floor_index,self.area,self.building_name,self.unit_code,self.unit_name,self.room_type,self.inner_index = tuple(df.fillna('None').to_list())
        self.form_DeviceList()

    def readDataBetween(self, start_time:str, end_time:str, datatype:str='P', time_interval=15):
        '''
        查询该房间在某段时间内的用电数据，时间格式：'2024-06-30 00:00:00'，返回室内空调用电、室外空调用电和其他电器用电，没有数据的返回0， 时间格式是时间戳，已除1000
        '''
        self.error_list = []
        self.empty_list = []
        self.time_interval = time_interval
        start_time_stamp = ReadData.str2timestamp(start_time)
        end_time_stamp = ReadData.str2timestamp(end_time)
        if self.room_type == '其他':
            return self.other_count(start_time_stamp, end_time_stamp)
        if self.room_type == '空调分摊':
            return self.ac_count(start_time_stamp, end_time_stamp)
        if self.room_type == '面积分摊':
            return self.area_count(start_time_stamp, end_time_stamp)
        if self.room_type == '空调面积分摊':
            return self.ax_area_count(start_time_stamp, end_time_stamp)

    def ac_count(self, start_time_stamp:int, end_time_stamp:int):
        '''
        空调分摊计算代码
        '''
        length = (end_time_stamp-start_time_stamp)//(self.time_interval*60)
        ac_inner = np.zeros(length)
        ac_outter = np.zeros(length)
        other = np.zeros(length)
        inner = np.zeros(length)
        df_in2out = pd.read_excel('设备档案/AC_Relationship.xlsx', sheet_name='每一个外机对应的内机')
        for i in range(len(self.inner_ac_device)):
            if self.outter_ac_device[i].isNoneDevice():
                continue
            inner_all = np.zeros(length)
            temp = df_in2out[df_in2out['室外分摊电表ID']==self.outter_ac_device[i].id].iloc[0,:].dropna().to_list()
            out_all = self.process_device(self.outter_ac_device[i], start_time_stamp, end_time_stamp)
            for j in temp:
                print(j)
                temp1 = self.process_device(Device(j), start_time_stamp, end_time_stamp)
                inner_all += temp1
                if j==self.inner_ac_device[i].id:
                    inner = temp1.copy()
            zero_both = np.intersect1d(np.where(inner_all==0), np.where(inner==0))
            # 某个内机和外机用电都是0的时候，按照1/2对室外机进行分摊
            inner[zero_both] = 1
            inner_all[zero_both] = 2
            ac_inner += inner
            ac_outter += out_all*inner/inner_all
        for device in self.other_device:
            other += self.process_device(device, start_time_stamp, end_time_stamp)
        print('Error List:', self.error_list)
        print('Empty List:', self.empty_list)
        return ac_inner, ac_outter, other

    def area_count(self, start_time_stamp:int, end_time_stamp:int):
        '''
        面积分摊计算代码
        '''
        length = (end_time_stamp-start_time_stamp)//(self.time_interval*60)
        inner_ac = np.zeros(length)
        outter_ac = np.zeros(length)
        other = np.zeros(length)
        for i in self.inner_ac_device:
            inner_ac += self.process_device(i, start_time_stamp, end_time_stamp)
        for i in self.outter_ac_device:
            outter_ac += self.process_device(i, start_time_stamp, end_time_stamp)
        for i in self.other_device:
            other += self.process_device(i, start_time_stamp, end_time_stamp)
        print('Error List:', self.error_list)
        print('Empty List:', self.empty_list)
        ratio = self.ratio_count()
        return inner_ac*ratio, outter_ac*ratio, other*ratio
    
    def ratio_count(self):
        area_info = pd.read_excel('设备档案/Device_Info.xlsx', sheet_name='面积分摊')
        if self.room_type == '面积分摊':
            area_info = area_info[area_info['内部索引']==self.inner_index].iloc[0,:]
        else:
            area_info = area_info[area_info['内部索引']==self.inner_index[6:]].iloc[0,:]
        room_list = area_info['子房间编号'].split('/')
        area_list = [float(x) for x in area_info['子房间面积'].split('/')]
        index = room_list.index(self.id)
        ratio = area_list[index]/sum(area_list)
        return ratio

    def other_count(self, start_time_stamp:int, end_time_stamp:int):
        '''
        其他类型房间计算代码
        '''
        length = (end_time_stamp-start_time_stamp)//(self.time_interval*60)
        inner_ac = np.zeros(length)
        outter_ac = np.zeros(length)
        other = np.zeros(length)
        for i in self.inner_ac_device:
            inner_ac += self.process_device(i, start_time_stamp, end_time_stamp)
        for i in self.outter_ac_device:
            outter_ac += self.process_device(i, start_time_stamp, end_time_stamp)
        for i in self.other_device:
            other += self.process_device(i, start_time_stamp, end_time_stamp)
        print('Error List:', self.error_list)
        print('Empty List:', self.empty_list)
        return inner_ac, outter_ac, other
    
    def ax_area_count(self, start_time_stamp:int, end_time_stamp:int):
        '''
        空调面积分摊类型房间计算
        '''
        inner_ac,outter_ac,other = self.ac_count(start_time_stamp, end_time_stamp)
        ratio = self.ratio_count()
        return inner_ac*ratio, outter_ac*ratio, other*ratio

    def process_device(self, device:Device, start_time_stamp:int, end_time_stamp:int):
        '''
        处理设备数据
        '''
        def form_data(x:pd.Series):
            global data
            index = x.name
            time1 = start_time_stamp + index*self.time_interval*60
            time2 = time1 + self.time_interval*60
            df_temp = df[(df['Time']>time1) & (df['Time']<time2)]
            if df_temp.empty:
                x[0] = np.nan
            else:
                data_temp = df_temp.iloc[:,1].to_numpy()
                time_temp = df_temp.iloc[:,0].to_list()
                pre_time = time_temp[0]-time1
                post_time = time2-time_temp[-1]
                data_temp_int = np.trapezoid(data_temp, time_temp)
                data_temp_int += data_temp[0]*pre_time+data_temp[-1]*post_time
                x[0] = round(data_temp_int/(time2-time1), 2)
        length = (end_time_stamp-start_time_stamp)//(self.time_interval*60)
        if device.isNoneDevice():
            return np.zeros(length)
        start_time = ReadData.timestamp2str(start_time_stamp)
        end_time = ReadData.timestamp2str(end_time_stamp)
        try:
            df = device.readDataBetween(start_time, end_time)
        except Exception as e:
            self.error_list.append(device.id)
            return np.zeros(length)
        if df.empty:
            self.empty_list.append(device.id)
            return np.zeros(length)
        else:
            data = pd.DataFrame(np.zeros((length,1)))
            data.apply(form_data, axis=1)
            data = data.iloc[:,0].to_numpy()
            b = np.interp(np.where(np.isnan(data))[0], np.where(~np.isnan(data))[0], data[~np.isnan(data)])
            data[np.where(np.isnan(data))[0]] = b
            data = np.round(data, 2)
            return data

    def form_DeviceList(self):
        '''
        生成房间设备列表
        '''
        category = {
            'ac':'空调分摊',
            'ar':'面积分摊',
            'ot':'其他'
        }
        self.inner_ac_device = []
        self.outter_ac_device = []
        self.other_device = []
        df = pd.read_excel('设备档案/Device_Info.xlsx', sheet_name=category[self.inner_index[:2]])
        if self.room_type == '空调面积分摊':
            info = df[df['内部索引']==self.inner_index[:5]].iloc[0,:].fillna('None')
        else:
            info = df[df['内部索引']==self.inner_index].iloc[0,:].fillna('None')
        if self.inner_index[:2] == 'ar':
            self.inner_ac_device.append(Device(info['室内空调电表'])) if info['室内空调电表'] != 'None' else self.inner_ac_device.append(Device('None'))
            self.outter_ac_device.append(Device(info['室外空调电表'])) if info['室外空调电表'] != 'None' else self.outter_ac_device.append(Device('None'))
            self.other_device = [Device(i) for i in info['其他电表'].split('/')]
        elif self.inner_index[:2]=='ac' or self.inner_index[:2]=='ot':
            self.inner_ac_device.append(Device(info['室内空调电表1 ID'])) if info['室内空调电表1 ID'] != 'None' else self.inner_ac_device.append(Device('None'))
            self.inner_ac_device.append(Device(info['室内空调电表2 ID'])) if info['室内空调电表2 ID'] != 'None' else self.inner_ac_device.append(Device('None'))
            self.outter_ac_device.append(Device(info['室外分摊电表1 ID'])) if info['室外分摊电表1 ID'] != 'None' else self.outter_ac_device.append(Device('None'))
            self.outter_ac_device.append(Device(info['室外分摊电表2 ID'])) if info['室外分摊电表2 ID'] != 'None' else self.outter_ac_device.append(Device('None'))
            self.other_device = [Device(i) for i in info['其他电表'].split('/')]

    def show_info(self):
        '''
        展示房间基础信息
        '''
        print(f"房间编号: {self.id}")
        print(f"房间号: {self.room_num}")
        print(f"楼层: {self.floor_index}")
        print(f"面积: {self.area}")
        print(f"所属楼宇名称: {self.building_name}")
        print(f"分配使用单元代码: {self.unit_code}")
        print(f"分配使用单元名称: {self.unit_name}")
        print(f"分摊类型: {self.room_type}")
        print(f"内部索引: {self.inner_index}")
        print('设备列表:')
        print('     室内空调电表: ', end='')
        for i in self.inner_ac_device:
            if not i.isNoneDevice():
                print(i.mac, end=' ')
        print('\n     室外空调电表: ', end='')
        for i in self.outter_ac_device:
            if not i.isNoneDevice():
                print(i.mac, end=' ')
        print('\n     其他电表: ', end='')
        for i in self.other_device:
            if not i.isNoneDevice():
                print(i.mac, end=' ')

class DataProcessor(object):
    def __init__(self) -> None:
        pass
    
    def process(self, data:np.ndarray, datatype:str='P')->np.ndarray:
        '''
        预处理数据，包括：
        1. 功率：
            1. 明显是出于测量误差的异常大---线性插值解决.
            2. 功率负数---线性插值处理；
        2. 电量：
            1. 电量猛增---对猛增点的增幅进行线性插值
            2. 累计电量减小---减小点的增幅进行线性插值
        3. 电流：
            1. 电流异常大---线性插值
            2. 电流为负数---线性插值
        4. 电压：
            1. 电压异常大
        '''
        if datatype in ['P', 'I', 'IA', 'IB', 'IC']:
            data = self.Fill_TooLarge(data, 5)
            data = self.Fill_Negative(data)
            return data
        if datatype in ['U', 'UA', 'UB', 'UC']:
            data = self.Fill_TooLarge(data, 2)
            return data
        if datatype=='Energy':
            data = self.Fill_SuddenIncrease(data)
            data = self.Fill_Decrease(data)
            return data

    def Fill_TooLarge(self, data:np.ndarray, times:int=5)->np.ndarray:
        '''
        处理数据中的异常大值
        '''
        mean = np.mean(data)
        data[np.where(data>mean*times)] = np.nan
        b = np.interp(np.where(np.isnan(data))[0], np.where(~np.isnan(data))[0], data[~np.isnan(data)])
        data[np.where(np.isnan(data))[0]] = b
        return np.round(data, 2)
    
    def Fill_Negative(self, data:np.ndarray)->np.ndarray:
        '''
        处理数据中的负数
        '''
        data[np.where(data<0)] = np.nan
        b = np.interp(np.where(np.isnan(data))[0], np.where(~np.isnan(data))[0], data[~np.isnan(data)])
        data[np.where(np.isnan(data))[0]] = b
        return np.round(data, 2)

    def Fill_SuddenIncrease(self, data:np.ndarray)->np.ndarray:
        '''
        处理功率数据中的猛增
        '''
        data_diff = np.diff(data)
        data_diff = self.Fill_TooLarge(data_diff, 5)
        return np.cumsum(data_diff)+data[0]

    def Fill_Decrease(self, data:np.ndarray)->np.ndarray:
        '''
        处理功率数据中的递减
        '''
        data_diff = np.diff(data)
        data_diff = self.Fill_Negative(data_diff)
        return np.cumsum(data_diff)+data[0]
        pass

# @st.cache_data
def GetRoomDataBetween(room_id, start_time:str, end_time:str, datatype:str='P', time_interval=15):
    '''
    读取房间在某个时间段的数据，时间格式：'2024-06-30 00:00:00'，返回数据时间格式是时间戳，已除1000
    '''
    room = Room(room_id)
    return room.readDataBetween(start_time, end_time, datatype, time_interval)

if __name__ == '__main__':
    # device = Device('Mt1-M1-a0764e56d490')
    # df = device.readDataBetween('2024-06-30 00:00:00', '2024-06-30 23:59:59')

    room = Room('seiee1306413267')
    print(room.readDataBetween('2024-06-30 00:00:00', '2024-06-30 23:59:59'))


