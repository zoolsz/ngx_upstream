from flask import Flask, render_template, request, jsonify, flash, redirect
from wtforms import Form, BooleanField, StringField
from wtforms.validators import DataRequired, IPAddress
import requests
import consul
import ast
import json
import re


app = Flask(__name__)

#
# @app.route('/')
# def hello_world():
#     return 'Hello World!'


ngx_servers = ['192.168.4.7/']


class AppenHostData(Form): #数据验证函数
    nginx_ip = StringField(u'所属nginx服务器地址', validators=[DataRequired()])
    upstream_dir = StringField(u'代理接口名称', validators=[DataRequired()])
    back_host = StringField(u'后端服务器地址', validators=[DataRequired(IPAddress())])
    back_Host_port = StringField(u'后端服务器器端口', validators=[DataRequired()])


def consul_conn(con_server='192.168.5.200', con_port='8500'): #连接consul服务器函数
    conn = consul.Consul(host=con_server, port=con_port, token=None, scheme='http', consistency='default', dc=None,
                         verify=True)
    return conn


def node_status(back_server, upstream_dir): #获取后端主机当前状态
    url = "http://{0}/{1}/monitor".format(back_server, upstream_dir)
    try:
        request_data = requests.get(url, timeout=5)
        request_status = request_data.status_code
        if request_status != 200:
            return 'Down'
        else:
            request_call = request_data.json()['succeed']
            if request_call:
                return 'UP'
    except Exception:
        return 'Down'


def HostList():
    con_server = '192.168.5.200'
    con_port = '8500'
    conn = consul_conn(con_server, con_port)
    host_list = []
    for s in ngx_servers:
        index, data = conn.kv.get(s, recurse=True)
        for d in data:
            options = ast.literal_eval(bytes.decode(d['Value']))
            # print(options)
            ngx_server = d['Key'].split('/')[0]
            upstream_dir = d['Key'].split('/')[1]
            back_server = d['Key'].split('/')[2]
            if 'weight' in options:
                weight = options['weight']
            else:
                weight = 0
            if 'max_fails' in options:
                max_fails = options['max_fails']
            else:
                max_fails = 0
            if 'fail_timeout' in options:
                fail_timeout = options['fail_timeout']
            else:
                fail_timeout = 0
            if 'down' in options and options['down'] == 1:
                back_status = 'Yes'
            else:
                back_status = 'No'
            if 'backup' in options and options['backup'] == 1:
                backup_status = 'ON'
            else:
                backup_status = 'OFF'
            status_check = node_status(back_server, upstream_dir)
            data2 = dict(back_host=back_server, ngx_server=ngx_server, upstream_table=upstream_dir, weight=weight,
                         max_fails=max_fails, fail_timeout=fail_timeout, status=back_status, backup=backup_status,
                         server_status=status_check)
            # print(data2)
            host_list.append(data2)
    return host_list


@app.route('/')
#获取主机列表
def index_status():
    host_list = HostList() #调用获取主机列表功能函数
    append_data = AppenHostData(request.form)
    return render_template('tables.html', host_list=host_list, form=append_data)


@app.route('/status_change', methods=['GET', 'POST'])
#手动修改主机为backup状态
def status_update():
    conn = consul_conn()
    html_data = request.get_json()
    print(html_data)
    host = html_data['data']
    index, data = conn.kv.get('{0}'.format(host))
    options = ast.literal_eval(bytes.decode(data['Value']))
    print(host)
    print(options)
    if 'status' in html_data:
        print(4567)
        status = html_data['status']
        if status == 'True':
            options['down'] = 0
        else:
            options['down'] = 1
    elif 'backup' in html_data:
        print(1234)
        backup = html_data['backup']
        if backup == 'True':
            options['backup'] = 1
        else:
            options['backup'] = 0
    print(options)
    print(host)
    consul_data = str(options).replace("'", '"')
    conn.kv.put(host, "{0}".format(consul_data))
    return jsonify({'status': 'success'})


@app.route('/weight_change',  methods=['GET', 'POST'])
#前端JQuery通过ajax删除后端主机
def weight_change():
    conn = consul_conn()
    html_data = request.get_json()
    print(html_data)
    host = html_data['data']
    weight = html_data['weight']
    index, data = conn.kv.get('{0}'.format(host))
    options = ast.literal_eval(bytes.decode(data['Value'])) #从consul服务器获取当前key的value值
    print(host)
    print(options)
    options['weight'] = weight #修改value值
    consul_data = str(options).replace("'", '"') #遍历数据为每个json中每个关键字的'变为"
    conn.kv.put(host, "{0}".format(consul_data))
    return jsonify({'status': 'success'})


@app.route('/append_back', methods=['GET', 'POST'])
#通过form表单添加主机
def append_back():
    #通过自定义累对form表单提交数据进行验证
    append_data = AppenHostData(request.form)
    #判断请求类型为POST请求
    if request.method == 'POST' and Form.validate:
        nginx_ip = '{0}/'.format(append_data.nginx_ip.data)
        BackHostPort = append_data.back_Host_port.data
        print(nginx_ip)#进行数据判断是否在nginx服务器列表中
        if nginx_ip not in ngx_servers:
            print(ngx_servers)
            print(nginx_ip)
            return redirect('/')
        upstream_dir = append_data.upstream_dir.data
        back_host = append_data.back_host.data
        conn = consul_conn()
        #拼接key字段
        consul_key = '{0}{1}/{2}:{3}'.format(nginx_ip, upstream_dir, back_host, BackHostPort)
        try:#添加key和value
            conn.kv.put(consul_key, '{"weight":1, "max_fails":0, "fail_timeout":0}')
            flash(u'添加成功！', 'success') #返回成功并返回/
            return redirect('/')
        except Exception:
            flash(u'添加失败！', 'failed')
            return redirect('/')
    flash(u'请正确输入数据', 'failed')
    return render_template('/')


@app.route('/host_delete',  methods=['GET', 'POST'])
#前端JQuery通过ajax删除后端主机
def host_delete():
    conn = consul_conn()
    #链接服务器
    html_data = request.get_json()
    #通过request获取传递参数 数据格式为json
    host = html_data['data']
    print(host)
    try:
        conn.kv.delete(host)
        return jsonify({'status': 'success'})
    except Exception:
        flash(u'添加失败！', 'failed')
        return jsonify({'status': 'failed'})


if __name__ == '__main__':
    app.debug = True
    app.secret_key = "aaaa"
    app.run()
