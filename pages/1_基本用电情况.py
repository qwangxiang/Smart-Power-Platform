import os
import sys
sys.path.append(os.getcwd())

import streamlit as st
import Login
import  DataProcess.Module as module
import pandas as pd

if __name__ == '__main__':
    authenticator,name,auth_status,username = Login.Login()
    if auth_status:
        if st.button('查询数据'):
            data = module.GetRoomDataBetween(username, '2024-06-30 00:00:00', '2024-07-01 00:00:00')
            df = pd.DataFrame(data[0].reshape(-1,1))
            st.write(df)