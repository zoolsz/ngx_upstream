from flask import Flask, render_template, request, jsonify, ext
from wtforms import Form, BooleanField, StringField, validators
import requests
import consul
import ast
import json

app = Flask(__name__)

#
# @app.route('/')
# def hello_world():
#     return 'Hello World!'

class AppenHostData(Form):
    nginx_ip = StringField('nginx_ip', [validators.DataRequired()])
    upstream_dir = StringField('upstream_dir', [validators.DataRequired()])
    back_host = StringField('back_host', [validators.DataRequired()])


def consul_conn(con_server='192.168.5.200', con_port='8500'):
    conn = consul.Consul(host=con_server, port=con_port, token=None, scheme='http', consistency='default', dc=None,
                         verify=True)
    return conn


def node_status(back_server, upstream_dir):
    url = "http://{0}/{1}/monitor".format(back_server, upstream_dir)
    print(url)
    try:
        request_data = requests.get(url, timeout=5)
        request_status = request_data.status_code
        print(request_status)
        if request_status != 200:
            return 'Down'
        else:
            request_call = request_data.json()['succeed']
            if request_call:
                return 'UP'
    except Exception:
        return 'Down'


@app.route('/')
def index_status():
    con_server = '192.168.5.200'
    con_port = '8500'
    ngx_servers = ['192.168.4.7/']
    conn = consul_conn(con_server, con_port)
    host_list = []
    for s in ngx_servers:
        index, data = conn.kv.get(s, recurse=True)
        for d in data:
            options = ast.literal_eval(bytes.decode(d['Value']))
            print(options)
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
            print(data2)
            host_list.append(data2)
    return render_template('tables.html', host_list=host_list)


@app.route('/status_change', methods=['GET', 'POST'])
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
def weight_change():
    conn = consul_conn()
    html_data = request.get_json()
    print(html_data)
    host = html_data['data']
    weight = html_data['weight']
    index, data = conn.kv.get('{0}'.format(host))
    options = ast.literal_eval(bytes.decode(data['Value']))
    print(host)
    print(options)
    options['weight'] = weight
    consul_data = str(options).replace("'", '"')
    conn.kv.put(host, "{0}".format(consul_data))
    return jsonify({'status': 'success'})


@app.route('/append_back', methods=['GET', 'POST'])
def append_back():
    append_data = AppenHostData(request.form)
    return render_template('tables.html', form=append_data)


if __name__ == '__main__':
    app.debug = True
    app.run()
