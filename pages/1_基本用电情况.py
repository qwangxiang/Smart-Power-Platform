import os
import sys
sys.path.append(os.getcwd())

import streamlit as st
import Login
import  DataProcess.Module as module
from DataProcess import ReadData
import pandas as pd
from pyecharts.charts import Bar,Line
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts
import time

def power_basic():
    st.header('基础用电情况展示')
    col1_1,col1_2,col1_3 = st.columns([0.5, 0.4, 0.1])
    default_time = ReadData.timestamp2str(int(time.time())-86400)[:10]
    date = default_time
    time_interval = 15
    with col1_1:
        date = str(st.date_input('请选择要查看的日期',value=pd.to_datetime(default_time)))
    with col1_2:
        time_interval = st.selectbox('请选择时间间隔（单位：分钟）', (5,15), index=1)
    with col1_3:
        check_button = st.button('查看')
    if check_button:
        data_inner,data_outter,data_other = module.GetRoomDataBetween(username, date+' 00:00:00', date+' 23:59:59', time_interval)
        time_axis = [str(i).zfill(2)+':00' for i in range(24)]
        figure = (
            Line()
            .add_xaxis(time_axis)
            .add_yaxis('空调内机用电', data_inner, stack='stack1', areastyle_opts=opts.AreaStyleOpts(opacity=0.5))
            .add_yaxis('空调外机用电', data_outter, stack='stack1', areastyle_opts=opts.AreaStyleOpts(opacity=0.5))
            .add_yaxis('其他设备用电', data_other, stack='stack1', areastyle_opts=opts.AreaStyleOpts(opacity=0.5))

            .set_global_opts(
                tooltip_opts=opts.TooltipOpts(is_show=True, trigger_on='mousemove', trigger='axis', axis_pointer_type='cross'),
                yaxis_opts=opts.AxisOpts(name='功率（W）', axislabel_opts=opts.LabelOpts(formatter='{value}W')),
                xaxis_opts=opts.AxisOpts(name='时间', axislabel_opts=opts.LabelOpts(interval=1)),
            )

            .set_series_opts(
                label_opts=opts.LabelOpts(is_show=False),
            )
        )
        st_pyecharts(figure)
    pass

def power_heatmap():
    st.header('用电热力图')
    pass

def energy_efficiency():
    st.header('能效分析')
    pass


if __name__ == '__main__':
    authenticator,name,auth_status,username = Login.Login()
    if auth_status:
        st.title('基础用电报告')

        power_basic()

        power_heatmap()

        energy_efficiency()
