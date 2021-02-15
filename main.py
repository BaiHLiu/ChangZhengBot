'''
Descripttion: 
version: 
Author: Catop
Date: 2021-02-10 07:47:09
LastEditTime: 2021-02-15 19:06:34
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
import random
import ocrplus
import inputFilter



app = Flask(__name__)
@app.route('/', methods=['POST'])
def getEvent():
    data = request.json
    post_type = data.get('post_type')
    if(post_type == 'message'):
        message_type = data.get('message_type')
        #print(data)
        message = data.get('message')
        user_id = str(data.get('user_id'))
        if(message_type=='private' and (dbconn.check_register(user_id)==1 or '注册' in message)):
            #仅接收注册用户的消息和注册消息
            print(f"--------------------\n接收消息@{user_id}:{message[:20]}")
            readMsg(user_id,message)
    elif(post_type == 'request'):
        request_type = data.get('request_type')
        if(request_type=='friend'):
            user_id = str(data.get('user_id'))
            comment = str(data.get('comment'))
            flag = str(data.get('flag'))
            print(f"--------------------\n接收加好友请求@{user_id}:{comment[:20]}")
            time.sleep(random.randint(5,10))
            goapi.add_request(flag)
            time.sleep(random.randint(5,10))
            goapi.sendMsg(user_id,"欢迎！\n请先注册，例如'注册@张三@信安20-2'\n 班级请严格按格式输入，否则可能统计不上哦")
    else:
        #暂不处理其他类型上报，为防止go-cq报错而设置
        pass
    

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
        
        }  #管理用户列表，只用于群提醒时找对应班级群号
    
    if('image' in message):
        if(dbconn.check_register(user_id)):
            #用户已注册
            get_img(user_id,message)
        else:
            #用户未注册
            goapi.sendMsg(user_id,'您还没注册呢，请输入例如"注册@张三@计科20-2"\n 班级请严格按格式输入，否则可能统计不上哦')
        return 
    if('注册' in message):
        try:
            user_name = message.split('@')[1]
            user_class = message.split('@')[2]
            #简单过滤用户输入
            if not(inputFilter.is_Chinese(user_name) and inputFilter.check_length(user_name)):
                goapi.sendMsg(user_id,'输入好像有点问题呢')
                return
            if not(inputFilter.is_valid(user_class) and inputFilter.check_length(user_class)):
                goapi.sendMsg(user_id,'输入好像有点问题呢')
                return
                
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
        user_class = dbconn.get_user(user_id)['user_class']
        upload_date = time.strftime("%Y-%m-%d", time.localtime()) 
        print(user_id)
        if(user_id in admin_list.keys()):
            group_id = admin_list[user_id]
            if('群提醒' in message):
                send_alert(group_id,dbconn.get_user(user_id)['user_class'],'group')
            elif('提醒'in message):
                send_alert(user_id,dbconn.get_user(user_id)['user_class'],'private')
                upload_date = time.strftime("%Y-%m-%d", time.localtime()) 
                time.sleep(1)
                #ocr_err_upload(user_id,user_class,upload_date)
                ocr_err_upload(user_id,user_class,upload_date)
                time.sleep(2)
                send_images_info(user_id,user_class)
            elif('打包'in message):
                cmp_ret = compress.zip_file(upload_date,dbconn.get_user(user_id)['user_class'])
                goapi.sendMsg(user_id,f"---打包完毕---\n共处理:{cmp_ret['file_num']}张照片")
                goapi.sendMsg(user_id,'下载地址:http://static.catop.top:8001/'+urllib.parse.quote(cmp_ret['file_name']))
            elif('成员'in message):
                list_class_menbers(user_id,user_class)
            else:
                goapi.sendMsg(user_id,"目前支持以下管理指令呢：\n群提醒\n提醒\n打包\n成员\n")
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
        
        download_img(img_url,file_name)
        #print(img_url)
    except Exception as err:
        goapi.sendMsg(user_id,'图片下载出错了！')
        print(err)
    else:
        print("成功处理图片:"+file_name)
        goapi.sendMsg(user_id,"成功处理图片，正在识别...\n"+file_name)

        """图片识别部分"""
        try:
            ocr_ret = ocrplus.ocr_img("images"+file_name)
            ocr_err_code = ocr_ret['err_code']
            if(ocr_err_code == 0):
                goapi.sendMsg(user_id,f"参赛次数:{ocr_ret['个人参赛次数']}\n个人积分:{ocr_ret['个人积分']}")
                ocr_times = ocr_ret['个人参赛次数']
                ocr_scores = ocr_ret['个人积分']
            else:
                #图片识别接口返回无法识别
                goapi.sendMsg(user_id,f"识别出错,请不要发送原图~问题不大，团支书将人工复核")
                dbconn.insert_img(user_id,file_name,upload_date,upload_time,'1','0','0')
                return 
        except:
            #图片识别接口出错
            goapi.sendMsg(user_id,f"识别出错,请不要发送原图~问题不大，团支书将人工复核")
            dbconn.insert_img(user_id,file_name,upload_date,upload_time,'1','0','0')
        else:
            dbconn.insert_img(user_id,file_name,upload_date,upload_time,ocr_err_code,ocr_times,ocr_scores)

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


    if(type=='private'):
        for user_id in alert_users.keys():
            last_date = alert_users[user_id]
            msg += f"{dbconn.get_user(user_id)['user_name']}({alert_users[user_id]})\n"
        msg+=f"{user_class} {current_date}\n完成情况:{len(group_menbers)-len(alert_users)}/{len(group_menbers)}"
        goapi.sendMsg(group_id,msg)
    elif(type=='group'):
        for user_id in alert_users.keys():
            last_date = alert_users[user_id]
            msg += f"[CQ:at,qq={user_id}]({alert_users[user_id]})\n"
        msg += f"{user_class} {current_date}\n完成情况:{len(group_menbers)-len(alert_users)}/{len(group_menbers)}"
        goapi.sendGroupMsg(group_id,msg)
    
def list_class_menbers(user_id,user_class):
    msg = f"{user_class}成员情况：\n"
    ret = dbconn.get_class_members(user_class)
    for i in range(0,len(ret)):
        msg += f"{ret[i]} {dbconn.get_user(str(ret[i]))['user_name']}\n"
    msg += f"共计{str(len(ret))}人"

    goapi.sendMsg(user_id,msg)
    

def ocr_err_upload(user_id,user_class,upload_date):
    """为管理员上报ocr错误的图片"""
    msg = "OCR无法识别以下图片:\n"
    err_list = []
    class_menbers = dbconn.get_class_members(user_class)
    for i in range(0,len(class_menbers)):
        img_date = dbconn.check_status(class_menbers[i])
        if(str(img_date) == str(upload_date)):
            img_info = dbconn.get_latest_img_info(class_menbers[i],upload_date)[0]
            #print(img_info)
            if(img_info['ocr_err_code'] == 1):
                print(img_info)
                err_list.append(img_info['file_name'])

    for i in range(0,len(err_list)):
        cqCode = f"[CQ:image,file=file:{os.getcwd()}/images{err_list[i]}]"
        msg += f"{cqCode}\n"
    msg += f"数量:{len(err_list)}/{len(class_menbers)}"

    goapi.sendMsg(user_id,msg)
    return msg

def send_images_info(user_id,user_class):
    """上报班级图片情况（次数和成绩）"""
    class_menbers = dbconn.get_class_members(user_class)
    today_upload_count = 0
    upload_date = time.strftime("%Y-%m-%d", time.localtime()) 
    msg = f"{user_class} {upload_date}情况:\n"
    for i in range(0,len(class_menbers)):
        if(str(dbconn.check_status(class_menbers[i])) == str(upload_date)):
            today_upload_count += 1
            img_info = dbconn.get_latest_img_info(class_menbers[i],upload_date)[0]
            if(img_info['ocr_err_code'] == 0):
                msg += f"·{dbconn.get_user(class_menbers[i])['user_name']} 次数{img_info['ocr_times']} 分数{img_info['ocr_scores']}\n"
            else:
                msg += f"·{dbconn.get_user(class_menbers[i])['user_name']} 未识别到\n"
    
    msg += f"共计{today_upload_count}张照片"

    goapi.sendMsg(user_id,msg)
    return msg



if __name__ == '__main__':
    app.run(host='127.0.0.1',port='5000',debug=False)
    #send_alert('1038368144','信安20-2','group')
    #goapi.sendMsg('29242764','[CQ:image,file=file:/Users/catop/Desktop/ChangZhengBot/go-cq/res1.png]')
    #print(ocr_err_upload('29242764','信安20-2','2021-02-13'))
    #goapi.sendMsg('29242764','[CQ:image,file=file:/Users/catop/Desktop/ChangZhengBot/images/2021-02-13/信安20-2/信安20-2班-张宏远-20210213.jpg]')
    #ocr_err_upload('601179193','信安20-2','2021-02-13')
    #print(send_images_info('29242764','信安20-2'))