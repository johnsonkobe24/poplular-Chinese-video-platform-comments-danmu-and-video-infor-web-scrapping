#!/usr/bin/env python
# coding: utf-8

# In[2]:


#Naimu Deng
#The bilibili has changed the format of their json script, this is the updated version for the new web-scraping
import numpy as np
import datetime
import csv
import os
from selenium import webdriver
import json
import itertools


# In[3]:


import requests
import re
import time
from bs4 import BeautifulSoup as BS
import urllib
import pandas as pd


# In[40]:


#use lumanati https superproxy integrated with selenium to prevent from IP blocking.

from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import *

PROXY = '127.0.0.1:24000'

proxy = Proxy()
proxy.http_proxy = PROXY
proxy.ftp_proxy = PROXY
proxy.sslProxy = PROXY
proxy.no_proxy = "localhost" 
proxy.proxy_type = ProxyType.MANUAL

#limunati customer info
proxy.socksUsername = 'lum-customer-hl_cc31cfbb-zone-static'
proxy.socksPassword = "f3n89y9at3tx"

capabilities = webdriver.DesiredCapabilities.CHROME

proxy.add_to_capabilities(capabilities)

driver = webdriver.Chrome(desired_capabilities=capabilities)
driver.get("https://passport.bilibili.com/login")


# In[5]:


#some notes:
#using chrome web developer tool to check the activity info
#bilibili has API portal and after check the web activity, cid json script is the key
#the cid bullet screen document is a xml document
#both http://comment.bilibili.com/xxxxxxx.xml and https://api.bilibili.com/x/v1/dm/list.so?oid=xxxxxxx will lead 
#the way to correct bullet screen comment page


# In[6]:


#set headers environment and encode url to html for later use
#user agent information is available at https://www.whoishostingthis.com/tools/user-agent/ 
def urltohtml(url):
        headers= {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',"Connection": "keep-alive","Cookie":""}
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        html = response.text
        return html


# In[7]:


#define the two way to decode web url
def get_selenium_cid(url):
    sevice_arguments = ['--load-images=false', '--disk-cache=true']
    #first you need to set default path
    driver = webdriver.PhantomJS(service_args = sevice_arguments,executable_path='/Users/johnson/Documents/phantomjs-2.1.1-macosx/bin/phantomjs')
    driver.get(url)
    #cid information is after "cid": and before ,
    cid = re.findall(r'"cid":(\d+),"page"', driver.page_source)[0]
    return cid
def get_cids(html):
    #analyzing json file, find that cid is located after "cid": in the list and before ,
    cid=re.findall(r'"cid":(\d+),"page"', html)
    return cid


# In[8]:


#defint a start function
def inputurl():
    url = input("Enter the video link : ")
    html = urltohtml(url)
    #using lxml processing XML and HTML in the Python.
    lxml = BS(html, 'lxml')
    #title and author info is under meta list
    title = lxml.select('meta[name="title"]')[0]['content']
    title=title
    author = lxml.select('meta[name="author"]')[0]['content']
    cid = get_cids(html)
    return cid,title,author


# In[9]:


#save to csv file
def savetocsv(info,title):
    header = ['appeartime', 'mode', 'font', 'color', 'posttime' ,'cluster', 'postid', 'rowID', 'content']
    #must encode with utf-8-sig to get correct chinese character
    with open('/Users/johnson/Desktop/DanmuDocuments/{}.csv'.format(title), 'w', newline='', errors='ignore',encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in info:
            writer.writerow(row)


# In[10]:


def standardizetime(time):
    #conver str to float first
    time=float(time)
    time=str(datetime.timedelta(seconds=time))
    return time


# In[11]:


def savetocsv_df(info,title):
    header = ['appeartime', 'mode', 'font', 'color', 'posttime' ,'cluster', 'postid', 'rowID', 'content']
    #must encode with utf-8-sig to get correct chinese character
    with open('/Users/johnson/Desktop/DanmuDocuments/{}.csv'.format(title), 'w', newline='', errors='ignore',encoding='utf-8-sig') as f:
            f.write('Custom String\n')
            info.to_csv(f, header=True, index=True)


# In[12]:


def time_time (start,end):
    dates=[]  
    date = start
    delta = datetime.timedelta(days=1)
    while date <= end:
        dates.append(str(date.strftime("%Y-%m-%d")))
        date += delta
    return dates


# In[13]:


#main function
#referring to:https://zhidao.baidu.com/question/1430448163912263499.html to interpret the key info from xml cid document
def getbulletscreencomments(start, end):
    dates=time_time(start,end)
    temp=inputurl()
    title=temp[1]
    cid_list=temp[0]
    l=1
    comments_info = pd.DataFrame()
    while l<len(cid_list):
        i=0
        cid=cid_list[l]
        while i < len(dates):
            comments_url = "https://api.bilibili.com/x/v2/dm/history?type=1&oid="+cid+"&date="+dates[i]
            driver.get(comments_url)
            comments_html = driver.find_element_by_tag_name('i').get_attribute('innerHTML')
            soup = BS(comments_html, 'lxml')
            data = pd.DataFrame([i.get('p').split(',') + [i.text] for i in soup.findAll('d')], columns=['appeartime', 'mode', 'font', 'color', 'posttime' ,'cluster', 'postid', 'rowID', 'content'])
            comments_info=comments_info.append(data)
            comments_info.drop_duplicates(inplace=True)
            i=i+1
        comments_info['appeartime']=int(round(comments_info['appeartime']))
        comments_info['appeartime']=pd.to_numeric(comments_info['appeartime'])
        comments_info['appeartime']= pd.to_timedelta(comments_info['appeartime'], unit='s')
        comments_info['posttime']=pd.to_datetime(comments_info['posttime'], unit='s')
        title_x=title+"{}".format(l)
        l=l+1
        print(l)
    return comments_info


# In[14]:


def getbulletscreencomments_one_video(start, end):
    dates=time_time(start,end)
    temp=inputurl()
    title=temp[1]
    cid_list=temp[0]
    l=0
    comments_info = pd.DataFrame()
    cid=cid_list[l]
    i=0
    while i < len(dates):
            comments_url = "https://api.bilibili.com/x/v2/dm/history?type=1&oid="+cid+"&date="+dates[i]
            driver.get(comments_url)
            comments_html = driver.find_element_by_tag_name('i').get_attribute('innerHTML')
            soup = BS(comments_html, 'lxml')
            data = pd.DataFrame([i.get('p').split(',') + [i.text] for i in soup.findAll('d')], columns=['appeartime', 'mode', 'font', 'color', 'posttime' ,'cluster', 'postid', 'rowID', 'content'])
            comments_info=comments_info.append(data)
            comments_info.drop_duplicates(inplace=True)
            i=i+1
            time.sleep(2)
    comments_info['appeartime']=pd.to_numeric(comments_info['appeartime'])
    comments_info['appeartime']= pd.to_timedelta(comments_info['appeartime'], unit='s')
    comments_info['posttime']=pd.to_datetime(comments_info['posttime'], unit='s')
    title_x=title+"{}".format(l)
    savetocsv_df(comments_info,title_x)
    return comments_info


# In[7]:


def getbulletscreencomments_naive():
    temp=inputurl()
    title=temp[1]
    cid_list=temp[0]
    l=0
    comments_info = pd.DataFrame()
    while l< 171:
            cid=cid_list[l]
            comments_url = 'http://comment.bilibili.com/{}.xml'.format(cid)
            comments_html = urltohtml(comments_url)
            soup = BS(comments_html, 'lxml')
            data = pd.DataFrame([i.get('p').split(',') + [i.text] for i in soup.findAll('d')], columns=['appeartime', 'mode', 'font', 'color', 'posttime' ,'cluster', 'postid', 'rowID', 'content'])
            comments_info=comments_info.append(data)
            l=l+1
    comments_info['appeartime']=pd.to_numeric(comments_info['appeartime'])
    comments_info['appeartime']= pd.to_timedelta(comments_info['appeartime'], unit='s')
    comments_info['posttime']=pd.to_datetime(comments_info['posttime'], unit='s')
    return comments_info
    


# In[37]:


start = datetime.date(2020,10,4)
end = datetime.date(2020,10,4)
a=getbulletscreencomments(start,end)

   


# In[41]:


start = datetime.date(2020,7,31)
end = datetime.date(2020,10,4)
b=getbulletscreencomments_one_video(start,end)


# In[63]:


c=getbulletscreencomments_naive()


# In[64]:


c


# In[320]:


b


# In[42]:


j=[b,c]
j=pd.concat(j)
j


# In[52]:


j['appeartime'] = j['appeartime'].astype(str)
j['appeartime'] = j['appeartime'].str[:-7]
j


# In[53]:


j['appeartime'] = j['appeartime'].str[7:-3]
j


# In[65]:


savetocsv_df(c,"大学数学2")


# In[25]:


def get_html():
        url = input("Enter the video link : ")
        headers= {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',"Connection": "keep-alive","Cookie":""}
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        html = response.text
        return html


# In[28]:


get_html()


# In[ ]:




