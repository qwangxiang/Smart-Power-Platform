import streamlit as st
import Login
import time

if __name__ == '__main__':
    authenticator,name,auth_status,username = Login.Login()
    if auth_status:
        st.title('欢迎来到智能用电系统！')
        st.write('id: ', name)
        st.write('auth_status: ', auth_status)
        st.write('username: ', username)
        st.write('功能正在开发中...')
        if st.button('click'):
            print(int(5.6))

