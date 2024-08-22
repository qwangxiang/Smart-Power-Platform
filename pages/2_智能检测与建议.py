import streamlit as st
import Login

def error_detect():
    st.header('故障检测')
    st.write('**功能开发中...**')
    pass

def power_predict():
    st.header('用电量预测')
    st.write('**功能开发中...**')
    pass

def power_advice():
    st.header('用电建议')
    st.write('**功能开发中...**')
    pass


if __name__ == '__main__':
    authenticator,name,auth_status,username = Login.Login()
    if auth_status:
        st.title('智能检测与建议')

        error_detect()

        power_predict()

        power_advice()
