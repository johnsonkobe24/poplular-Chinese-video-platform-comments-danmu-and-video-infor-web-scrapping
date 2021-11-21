#!/usr/bin/env python
# coding: utf-8

# In[12]:


#Naimu Deng
#danmu package is use instead of connecting using DouYu API
#customized danmu package for implicaity
import time 
import sys 
import danmu
import numpy as np
import csv
import os
import pymongo
from pymongo import MongoClient
import json
import requests
import re
import csv
from bs4 import BeautifulSoup as BS
import pandas as pd


# In[13]:


os.chdir("/Users/johnson/Desktop")
os.getcwd()


# In[14]:


#this is the livestreaming updating program, so we need database to install each data instantly, unlike the other 2
#create a pymongo database
#follow official website https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/ to install mongodb
#start brew services start mongodb-community@4.2 everytime
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
#create a database
db = myclient['database']
#create a collection for use
DouYu=db["DouYu"]


# In[15]:


#convert url to html and get room name from it 
def urltohtml(url):
        headers= {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        html = response.text
        return html


# In[16]:


#find title info
def find_name(url):
    html=urltohtml(url)
    lxml = BS(html, 'lxml')
    title = lxml.select('title')
    #convert BS tag to str to trim tag
    title=title[0].get_text()
    return title


# In[17]:


#save data to a dict and convert it to list then append as dataframe then save to csv file
def save_to_csv(title):
    data=[]
    cursor = DouYu.find()
    #pick certain keys to exclude database objectid, and convert it to string
    for document in cursor:
        result = dict((k,document[k]) for k in ['user_name', 'data_type','chat_text']
                                           if k in document)
        result=list(result.values())
        data.append(result)
        df = pd.DataFrame(data)
        df.columns = ['user_name', 'data_type','chat_text']
    df.to_csv(r'/Users/johnson/Desktop/{}.csv'.format(title), encoding='utf-8-sig',index=False)
    print(df)


# In[18]:


#main function
def get_comment_info():
    url = input("Enter the room url : ")
    title=find_name(url)
    #create a mongo collection inside the database
    #get info from danmu
    bulletscreen=danmu.DanMuClient(url)
    #set function inside the decorators
    @bulletscreen.danmu
    def danmu_fn(msg):
            chat_data = {
                        "user_name": msg['NickName'],
                        "data_type": msg['MsgType'],
                        "chat_text": msg['Content']
                        }
            DouYu.insert_one(chat_data)
    @bulletscreen.gift
    def gift_fn(msg):
            gift_data = {
                        "user_name": msg['NickName'],
                        "data_type": msg['MsgType'],
                        "chat_text": 'sent a gift!'
                        }
            DouYu.insert_one(gift_data)
    bulletscreen.start(blockThread = True)
    save_to_csv(title)
    #clear database for the next time use
    db.DouYu.drop()


# In[ ]:


get_comment_info()


# In[ ]:





# In[ ]:




