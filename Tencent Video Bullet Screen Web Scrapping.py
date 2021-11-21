#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Naimu Deng
#the tencent platform has changed its json configuration, this is the most updated working program
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


# In[2]:


#note: when analyzing tencent video through Chrome Brower , I found that tencent bullet screen is under
#https://mfm.video.qq.com/danmu?otype=json json request, therefore, we can do something to get the comments. 


# In[3]:


#set headers environment and encode url to html for later use
#user agent information is available at https://www.whoishostingthis.com/tools/user-agent/ 
#return title too
def urltohtml():
        url = input("Enter the video link : ")
        headers= {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        html = response.text
        lxml_temp=BS(html,'lxml')
        title = lxml_temp.select('meta[name="twitter:title"]')[0]['content']
        title
        return html,title


# In[4]:


#In order to get comments from all episodes in a TV series, we must build a loop to check every episodes 
#which needs episodes ID and comment target ID, which are stored in JS and XHR document. 
#the episodes ID is just in the json html document in the vid element which include all original episodes and its highlights
#However if it is a reality show, the vid list only includes the full video of that particular episode 
#as well as the all the highlight videos of that particular episodes, 
#so we still need to type in the url one by one for whole reality show series
#this is due to tencent video platform own regulation, no way to fix that...
def get_vid_id (html):
    #vidid are located at nomal_ids list
    list_id=re.search(r'"vid":(.*?)]',html,re.S).group(1)+"]"
    list_id=json.loads(list_id)
    return list_id 


# In[5]:


#this is the classic way to find episodes id in nomal_ids element but that only include original full video
#and exclude all the highlights
#however for reality shows, this way still include highlights of that particular episodes...
#here we use only_episode_id for the rest of the program
def get_only_episode_vid(html):
    nomal_id=re.search(r'"nomal_ids":(.*?)]',html,re.S).group(1)+"]"
    nomal_id=json.loads(nomal_id)
    list_id=[]
    for i in nomal_id:
        if i["F"]!=0:
            list_id.append(i["V"])
    return list_id


# In[6]:


#some notes
#with vid_ids, we can find corresponding target_id
#the corresponding target_id is under a XHR document and it is a post request
#moreover vesecret is also unchanged "c0bdcbae120669fff425d0ef853674614aa659c605a613a4", so the post url has its standard format
#https://access.video.qq.com/danmu_manage/regist?vappid=[vappid]&vsecret=[vsecret]&row=1
#however, html does not contain vappid info, so we still need to include that mannually.
#the original regist document has strcid and strlid configuration, however, i found they are not affecting the targetid
#return so i discarded that 


# In[7]:


#loop to get all target id and vid set
def get_target_id (vid,auth_url):
    target_id_list=[]
    #configure the parameters in json according to the request payload
    headers= {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'}
    html_regist = requests.post(auth_url, data = json.dumps({'wRegistType': 2, 'vecIdList': [vid], 'wSpeSource': 0, 'bIsGetUserCfg': 1}), headers=headers)
    html_regist=html_regist.text
    result = json.loads(html_regist) 
    target_key=result['data']["stMap"][vid]["strDanMuKey"]
    target_id=target_key[target_key.find('targetid') + 9 : ] 
    return target_id,vid


# In[8]:


#loop to get all target id and vid set
def get_targetid_vid_pairs(html):
    info_pairs=[]
    vid=get_only_episode_vid (html)
    i=0
    auth_url = input("Enter the regist url : ")
    for i in vid:
        pairs = get_target_id (i,auth_url)
        info_pairs.append(pairs)
    return info_pairs


# In[9]:


#converting time in seconds to standard time format
def standardizetime(time):
    #conver str to float first
    time=float(time)
    time=str(datetime.timedelta(seconds=time))
    return time


# In[10]:


#now we are able to get the whole bullet screen urls, which is in the standard format start with 
#https://mfm.video.qq.com/danmu?and configured by timestamp target id and vid, the rest are useless and can ignore
#for timestamp, the count=0 when there is no comment, so getting whole comments for one episode is easy
def get_comments_basic(target_id, vid, timestamp):
    bullet_url="https://mfm.video.qq.com/danmu?target_id={}%26vid%3D{}&timestamp={}".format(target_id,vid,timestamp)
    comment_result=requests.get(bullet_url,headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'}).json(strict=False)
    data=pd.DataFrame()
    for i in comment_result['comments']:
        #there are many information, i only get one that i need. 
            comment_style=i['content_style']
            content=i['content']
            name=i['opername']
            upvotes=i['upcount']
            vipdegree=i['uservip_degree']
            time=i['timepoint']
            time=standardizetime(time)
            data_temp={'Username':[name],'Content':[content],'Vip Degree':[vipdegree],'Post Time':[time],'Up Votes':[upvotes],'Comment Style':[comment_style]}
            #sort as dict
            data_temp=dict(sorted(data_temp.items(),key=lambda x:x[0]))
            data_temp=pd.DataFrame(data_temp)
            data=data.append(data_temp)
    return data
    


# In[11]:


#now get whole comment for one episode
def get_comments_one_episodes(target_id,vid):
    timestamp=15
    comment_data=pd.DataFrame()
    while get_comments_basic(target_id, vid, timestamp).empty!= True:
            comment_data_temp= get_comments_basic(target_id, vid, timestamp)
            comment_data=comment_data.append(comment_data_temp)
            timestamp+=30
    else:
            print('Loop done on one episode')
    return comment_data


# In[12]:


#loop everything together to get the whole bullet screen comments for all episodes
def get_all_bullet_screen_comments():
    url=urltohtml()
    html=url[0]
    title=url[1]
    param_pairs=get_targetid_vid_pairs(html)
    comments_dataframe=pd.DataFrame()
    for i in param_pairs:
        comments_dataframe_temp=get_comments_one_episodes(i[0],i[1])
        comments_dataframe=comments_dataframe.append(comments_dataframe_temp)
    comments_dataframe.to_csv(r'/Users/johnson/Desktop/{}.csv'.format(title), encoding='utf-8-sig')
    
        
        
    
    


# In[14]:


get_all_bullet_screen_comments()


# In[ ]:




