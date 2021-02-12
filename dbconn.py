'''
Descripttion: 
version: 
Author: Catop
Date: 2021-02-10 09:10:27
LastEditTime: 2021-02-12 23:17:55
'''
#coding:utf-8
import pymysql

'''连接数据库配置'''
conn = pymysql.connect(host='192.168.123.180',user = "qqbot",passwd = "HX5sweAyk3KJdStN",db = "qqbot")


def check_cmd(user_id):
    #获取最近一条命令
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    #结果返回dict
    sql = f"SELECT last_cmd FROM userinfo WHERE user_id={user_id} LIMIT 1"
    conn.ping(reconnect=True)
    cursor.execute(sql)
    last_cmd = cursor.fetchone()['last_cmd']
    conn.commit()
    
    return last_cmd


def check_register(user_id):
    #检查用户是否注册
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = f"SELECT uid FROM userinfo WHERE user_id={user_id} LIMIT 1"
    conn.ping(reconnect=True)
    cursor.execute(sql)
    user_info = cursor.fetchall()
    conn.commit()

    if(len(user_info)>=1):
        return 1
    else:
        return 0

def insert_img(user_id,file_name,upload_date,upload_time,ocr_err_code,ocr_times,ocr_scores):
    params = [file_name,user_id,upload_date,upload_time,ocr_err_code,ocr_times,ocr_scores]
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = f"INSERT INTO imginfo(file_name,user_id,upload_date,upload_time,ocr_err_code,ocr_times,ocr_scores) VALUES(%s,%s,%s,%s,%s,%s,%s)"
    conn.ping(reconnect=True)
    cursor.execute(sql,params)
    conn.commit()

    return 


def get_user(user_id):
    #获取用户姓名和班级
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = f"SELECT user_name,user_class FROM userinfo WHERE user_id={user_id} LIMIT 1"
    conn.ping(reconnect=True)
    cursor.execute(sql)
    user_info = cursor.fetchone()
    conn.commit()

    return user_info




def register_user(user_id,user_name,user_class):
    #注册新用户

    try:
        params = [user_id,user_name,user_class]
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        sql = f"INSERT INTO userinfo(user_id,user_name,user_class) VALUES(%s,%s,%s)"
        conn.ping(reconnect=True)
        cursor.execute(sql,params)
        conn.commit()
    except:
        flag=0
    else:
        flag=1


    return flag

def re_register_user(user_id,user_name,user_class):
    #重新注册，更新用户信息
    try:
        params = [user_name,user_class,user_id]
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        sql = f"UPDATE userinfo SET user_name=%s,user_class=%s WHERE user_id=%s"
        conn.ping(reconnect=True)
        cursor.execute(sql,params)
        conn.commit()
    except:
        flag=0
    else:
        flag=1
    
    return flag

def check_today_upload(user_id,upload_date):
    #检查用户当日是否已经上传过
    user_id = str(user_id)
    upload_date = str(upload_date)
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = f"SELECT imgid FROM imginfo WHERE(user_id={user_id} AND upload_date='{upload_date}')"
    conn.ping(reconnect=True)
    cursor.execute(sql)
    if(len(cursor.fetchall())>=1):
        return 1
        conn.commit()
    else:
        return 0
        conn.commit()

def check_status(user_id):
    #返回指定用户最新一条记录的时间
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    sql = f"SELECT upload_date FROM imginfo WHERE user_id={user_id} ORDER BY upload_date DESC LIMIT 1"
    conn.ping(reconnect=True)
    cursor.execute(sql)
    last_date = cursor.fetchone()['upload_date']
    conn.commit()
    
    return last_date

def get_class_members(user_class):
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    params = [user_class]
    sql = f"SELECT user_id FROM userinfo WHERE user_class=%s"
    conn.ping(reconnect=True)
    cursor.execute(sql,params)
    sql_ret = cursor.fetchall()
    conn.commit()
    class_menbers = []

    for i in range(0,len(sql_ret)):
        class_menbers.append(sql_ret[i]['user_id'])
    return class_menbers




if __name__=='__main__':
    print(get_user(601179193))
    #insert_img('601179193','test.jpg','2021-02-10','09:47:49')
    #print(check_today_upload('601179193','2021-02-10'))
    #print(register_user('29242764','李四','信安20-1'))
    print(check_status(601179193))
    print(get_class_members('信安20-2'))