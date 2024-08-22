import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Hasher

# 常用用户1：admin 密码：admin ---管理员权限
# 常用用户2：seiee1306413267 密码：abcdef ---普通用户权限
# 常用用户3：seiee1391313964 密码：abcdef ---3205-普通用户权限
# 常用用户4：seiee1391313926 密码：abcdef ---3105-普通用户权限

def Login():
    with open('UserConfig.yaml') as f:
        config = yaml.load(f, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['pre-authorized'],
        auto_hash=False
    )
    name,auth_satus,username = authenticator.login()
    if auth_satus:
        with st.sidebar:
            authenticator.logout()
    elif auth_satus is False:
        st.error('Username/password is incorrect')
    elif auth_satus is None:
        st.warning('Please enter your username and password')
    return authenticator,name,auth_satus,username





