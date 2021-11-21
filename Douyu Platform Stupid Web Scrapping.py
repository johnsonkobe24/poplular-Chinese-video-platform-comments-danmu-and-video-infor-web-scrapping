#!/usr/bin/env python
# coding: utf-8

# In[2]:


#Naimu Deng
#Douyu Api has open protocol, we are able to connect to Douyu LiveStream Room to get the bullet screen 
import numpy as np
import datetime
import csv
import os
import requests
import re
import time
from bs4 import BeautifulSoup as BS
import urllib
from urllib import parse
import json
import pandas as pd
import socket
import logging
import threading
import signal
import multiprocessing


# In[3]:


#configure server log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# In[4]:


#connect API
self = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostbyname("openbarrage.douyutv.com")
#8601、8602、12601、12602 all possible
port= 8601
self.connect((host, port))


# In[4]:


#evaluate API protocal message format
def send_api_msg(msg):
    msg=msg+'\0'
    msg=msg.encode('utf-8')
    length=len(msg)+8
    #code is 689 indicating message type
    code=689
    #setting head
    head=int.to_bytes(length,4,'little')+int.to_bytes(length,4,'little')+int.to_bytes(code,4,'little')
    self.send(head)
    message_sent=0
    while message_sent < len(msg):
        n=self.send(msg[message_sent:])
        message_sent=message_sent+n


# In[5]:


#set a stop handler
def signal_handler(signal,frame):
            p1.terminate()
            p2.terminate()
            logout()


# In[6]:


#get it alive
def keep_alive():
    while True:
        keep_msg = "mrkl/"  
        send_api_msg(keep_msg)
        time.sleep(40)
        logging.info("Keep Alive")


# In[7]:


#get comments
def get_comments (room_id):
    login(room_id)
    while True:
        try:
            data = self.recv(2048)
            data = data[12:].decode('utf-8', 'ignore')
            if re.search('type@=chatmsg', data):
                pattern1 = re.compile('uid@=(.+?)/nn@=(.+?)/txt@=(.+?)/cid@=(.+?)/')
                chat = re.findall(pattern1, data)[0]
                print(chat)
            time.sleep(0.05) 
        except KeyError:
            pass
        except Exception as Except:
            logging.info(Except)
    return chat


# In[8]:


#logout
def logout():
    out_msg = 'type@=logout/'
    send_api_msg('type@=logout/')
    logging.info('log out seccessfully')


# In[9]:


#log into api
def login (room_id):
    login_msg = "type@=loginreq/roomid@={}/".format(room_id)
    send_api_msg(login_msg)
    join_msg = "type@=joingroup/rid@={}/gid@=-9999/".format(room_id)
    send_api_msg(join_msg)
    logging.info("Succeed in logging in.")


# In[10]:


if __name__ == '__main__':
    room_id=3014399
    #signal.signal(signal.SIGINT,signal_handler)
    #p1 = multiprocessing.Process(target = get_comments,args = (room_id,))
    #p2 = multiprocessing.Process(target = keep_alive)
    #p1.start()
    #p2.start()
    t = threading.Thread(target=keep_alive)
    #set a deamon thread exit
    t.setDaemon(True)  
    t.start()
    while True:
        t1 = threading.Thread(target=get_comments, args=(room_id,))
        t1.start()
        t1.join()


# In[ ]:




