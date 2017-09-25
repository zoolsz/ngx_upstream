import consul
import ast
import requests
import json

c = consul.Consul(host='192.168.5.200', port=8500, token=None, scheme='http', consistency='default', dc=None,
                  verify=True)
# c.kv.put('foo/test/10.0.0.2:8080', '{"weight":1, "max_fails":2, "fail_timeout":10}')
#
# index, data = c.kv.get('upstream', recurse=True)
# print(data)
# c.kv.put('192.168.4.7/prod-app/192.168.4.116:8080', '{"weight":1, "max_fails":0, "fail_timeout":10, }')
# c.kv.put('192.168.4.7/prod-app/192.168.4.116:8080', '3')
# k, v1 = c.kv.get('192.168.4.7/prod-app/192.168.4.116:8080')
# v2 = c.kv.get('192.168.4.7/prod-app/192.168.4.116:8080')
# print(type(v1['Value']))
# print(type(v1))
# print(type(v2))

dict_test = {'down': 1, 'max_fails': 10, 'weight': 1, 'fail_timeout': 100}
str_test = str(dict_test).replace("'", '"')
print(str_test)
# help(c.kv.get)

# print(index)
# for d in data:
#     options = ast.literal_eval(bytes.decode(d['Value']))
    # print(d)
    # print(d['Key'])
    # print(type(options))
    # print(d['Value']['weight'])
    # print(options)
    # print(d['Key'].split('/')[2])
    # print(type(d['Value']))
# print(data)

#
# back_server = '192.168.4.111:8080'
# upstream_dir = 'acc-app'
# url = "http://{0}/{1}/monitor".format(back_server, upstream_dir)
# print(url)
# request_data = requests.get(url)
# print(request_data.json()['succeed'])
# if request_data.json()['succeed'] and request_data.status_code == '200':
#     print('yes')
# else:
#     print('NO')
# print(type(request_data.status_code))




# c.query.list(dc='dc1')