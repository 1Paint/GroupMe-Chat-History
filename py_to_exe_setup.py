from distutils.core import setup
import py2exe

setup(windows=['get_chat_history_v1.1.py'], options={"py2exe":{"includes":["sip"]}})
