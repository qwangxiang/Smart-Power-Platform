import os
import sys
sys.path.append(os.getcwd())

import streamlit as st
import Login
from DataProcess.Module import Room

if __name__ == '__main__':
    authenticator,name,auth_status,username = Login.Login()