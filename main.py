'''
Descripttion: 
version: 
Author: Catop
Date: 2021-02-10 07:47:09
LastEditTime: 2021-02-10 22:02:01
'''
#coding:utf-8

from flask import Flask,request,jsonify
import json
import requests
import dbconn
import goapi
import time
import os
import compress
import urllib.parse



app = Flask(__name__)
@app.route('/', methods=['POST'])
def getEvent():
    data = request.json
    post_type = data.get('post_type')
    message_type = data.get('message_type')
    #print(data)
    message = data.get('message')
    user_id = data.get('user_id')
    user_id = str(user_id)
    print(f"--------------------\n接收消息@{user_id}：{message[:20]}")

    if(post_type=='message' and message_type=='private'):
        #print(f"user_id:{user_id} message:{message}")
        readMsg(user_id,message)
        
    return data

def readMsg(user_id,message):
    #处理消息核心
    user_id = str(user_id)
    admin_list = {
        '601179193':'949773437',
        '29242764':'1038368144',
        '1251248524':'949773437',
        '2766104656':'515192555',
        '20475417':'515192555'
        
        }  #管理用户列表
    
    if('image' in message):
        if(dbconn.check_register(user_id)):
            #用户已注册
            get_img(user_id,message)
        else:
            #用户未注册
            goapi.sendMsg(user_id,'您还没注册呢，请输入例如"注册@张三@信安20-2"  班级请严格按格式输入，否则可能统计不上哦')
        return 
    if('注册' in message):
        try:
            user_name = message.split('@')[1]
            user_class = message.split('@')[2]
        except:
            goapi.sendMsg(user_id,'输入好像有点问题呢')
        else:
            if(dbconn.check_register(user_id)):
                goapi.sendMsg(user_id,'您已注册过啦~')
                re_register_user(user_id,user_name,user_class)
            else:
                    register_user(user_id,user_name,user_class)
        return 
    if('/admin' in message):
        print(user_id)
        if(user_id in admin_list.keys()):
            group_id = admin_list[user_id]
            if('群提醒' in message):
                send_alert(group_id,dbconn.get_user(user_id)['user_class'],'group')
            elif('提醒'in message):
                send_alert(user_id,dbconn.get_user(user_id)['user_class'],'private')
            elif('打包'in message):
                upload_date = time.strftime("%Y-%m-%d", time.localtime()) 
                cmp_ret = compress.zip_file(upload_date,dbconn.get_user(user_id)['user_class'])
                goapi.sendMsg(user_id,f"---打包完毕---\n共处理:{cmp_ret['file_num']}张照片")
                goapi.sendMsg(user_id,'下载地址:http://static.catop.top:8001/'+urllib.parse.quote(cmp_ret['file_name']))
            else:
                goapi.sendMsg(user_id,"管理指令有误")
        else:
            
            goapi.sendMsg(user_id,"无管理权限")
        
        return 

                
        
            
def get_img(user_id,message):
    #从message中解析到图片下载地址，并保存数据库，下载文件
    try:
        img_url = message.split('url=')[1][0:-1]
        user_name = dbconn.get_user(user_id)['user_name']
        user_class = dbconn.get_user(user_id)['user_class']
        upload_date = time.strftime("%Y-%m-%d", time.localtime()) 
        upload_time = time.strftime("%H:%M:%S", time.localtime()) 

        #修改文件名格式(注意只保存文件名和数据库中显示的file_name改变，目录等名称不变)
        file_date = time.strftime("%Y%m%d", time.localtime()) 

        #判断文件目录是否存在
        if not(os.path.exists(f"images/{upload_date}")):
            os.mkdir(f"images/{upload_date}")
        if not(os.path.exists(f"images/{upload_date}/{user_class}")):
            os.mkdir(f"images/{upload_date}/{user_class}")

        file_name = f"/{upload_date}/{user_class}/{user_class}班-{user_name}-{file_date}.jpg"
        if(dbconn.check_today_upload(user_id,upload_date)):
            goapi.sendMsg(user_id,'您今天已经上传过照片啦，已覆盖之前的图片~')
        
        dbconn.insert_img(user_id,file_name,upload_date,upload_time)
        download_img(img_url,file_name)
        #print(img_url)
    except Exception as err:
        goapi.sendMsg(user_id,'图片下载出错了！')
        print(err)
    else:
        print("成功处理图片:"+file_name)
        goapi.sendMsg(user_id,"成功处理图片:"+file_name+" 祝生活愉快~")
    return 


def download_img(img_url,file_name):
    res = requests.get(img_url, stream=True)
    if res.status_code == 200:
        open('images/'+file_name, 'wb').write(res.content)
        #print("image"+file_name+"saved successfully.")

def register_user(user_id,user_name,user_class):
    if(dbconn.register_user(user_id,user_name,user_class) == 1):
        goapi.sendMsg(user_id,'注册成功，现在可以开始上传图片了~')
    else:
        goapi.sendMsg(user_id,'注册失败'+f"user_id={user_id},user_name={user_name},user_class={user_class}")
        
def re_register_user(user_id,user_name,user_class):
    if(dbconn.re_register_user(user_id,user_name,user_class) == 1):
        goapi.sendMsg(user_id,'已更新字段')
    else:
        goapi.sendMsg(user_id,'更新字段失败:'+f"user_id={user_id},user_name={user_name},user_class={user_class}")


def send_alert(group_id,user_class,type='private'):
    group_menbers = dbconn.get_class_members(user_class)
    current_date = time.strftime("%Y-%m-%d", time.localtime()) 
    alert_users = {}
    #user_id:last_date
    for user_id in group_menbers:
        #print(user_id)
        try:
            last_date = dbconn.check_status(user_id)
        except TypeError:
            #还没发过照片
            alert_users[user_id] = '无记录'
        else:
            if(str(last_date)!=str(current_date)):
                alert_users[user_id] = str(last_date)[5:]
    
    #print(alert_users)
    msg = f"今天还有{len(alert_users)}位小可爱未完成哦\n"
    for user_id in alert_users.keys():
        last_date = alert_users[user_id]
        msg += f"[CQ:at,qq={user_id}]({alert_users[user_id]})\n"
    msg+=f"{user_class} {current_date} {len(group_menbers)-len(alert_users)}/{len(group_menbers)}"

    if(type=='private'):
        goapi.sendMsg(group_id,msg)
    elif(type=='group'):
        goapi.sendGroupMsg(group_id,msg)


    


if __name__ == '__main__':
    app.run(host='127.0.0.1',port='5000',debug=False)
    #send_alert('1038368144','信安20-2','group')