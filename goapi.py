'''
Descripttion: 
version: 
Author: Catop
Date: 2021-02-10 09:38:39
LastEditTime: 2021-02-10 20:37:44
'''
#coding:utf-8
import requests



def sendMsg(user_id,message):
    url = 'http://127.0.0.1:5800/send_private_msg'
    data = {'user_id':user_id,'message':message}
    res = requests.get(url,params=data)
    print(f"--------------------\n回复私聊消息@{user_id}：{message[:20]}")
    return res.text

def sendGroupMsg(group_id,message):
    url = 'http://127.0.0.1:5800/send_group_msg'
    data = {'group_id':group_id,'message':message}
    res = requests.get(url,params=data)
    print(f"--------------------\n回复群消息@{group_id}：{message[:20]}")
    return res.text

def uploadGroupFile(group_id,file_dir,file_name):
    url = 'http://127.0.0.1:5800/upload_group_file'
    #data = {'group_id':group_id,'file':file_dir,'file_name':file_name}
    file = file_dir+'/'+file_name
    data = {'group_id':group_id,'file':file}
    res = requests.get(url,params=data)
    print(f"--------------------\n上传群文件@{group_id}：{file}")
    return res.text



if __name__=='__main__':
    #sendMsg('601179193','test')
    #sendGroupMsg('1038368144','信安20-2')
    print(uploadGroupFile('1038368144','../compressed','2021-02-10_信安20-2_20_17_19.zip'))