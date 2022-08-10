 # vim: set fileencoding=utf-8

from flask import Flask, request
import json
import requests
import time
import datetime

app = Flask(__name__)


@app.route('/api/v1_deta', methods=["GET"])

def start():
   args = request.args

   pool_id= args.get('pool_id')


   day=3
   time_end = datetime.datetime.now()      
   time_start= (datetime.datetime.now() - datetime.timedelta(days = day))  
       
   time_end = time_end.strftime("%Y-%m-%d %H:%M:%S")      
   time_start=time_start.strftime("%Y-%m-%d %H:%M:%S")


#   将时间换华为时间数组
   timeArray1 = time.strptime(time_start, "%Y-%m-%d %H:%M:%S")
   # 转换为时间戳:
   time_start_timeStamp = int(time.mktime(timeArray1))


   timeArray2 = time.strptime(time_end, "%Y-%m-%d %H:%M:%S")

   time_end_timeStamp = int(time.mktime(timeArray2))

   def run_query(query):
      """
      Function: run_Query
      return: 返回JSON格式数据
      """

      request = requests.post('https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-subgraph', json={'query': query})
      if request.status_code == 200:
         return request.json()
      else:
         raise Exception('Query failed. return code is {}.'.format(request.status_code))

   def json_push(x):          #要提交的json
      return f'''
      query MyQuery {{
      swaps(
         where: {{pool: "{pool_id}" timestamp_gte: "{x}" }}
         orderBy: timestamp
         orderDirection: asc
         first: 1000
      ) {{
         tick
         timestamp
         id
      }}
      }}
      '''
      
   data_all = []    #用于存放所有数据，存在时间戳和id重复




   ts = time_start_timeStamp

   while ts < time_end_timeStamp:    
      json_get = run_query( json_push(ts) )
      data = [json_get['data']['swaps'][i] for i in range(0,len(json_get['data']['swaps']))]    #将目标数据改为一个个字典形式，存入data列表
      data_all.append(data)   
      ts = int(data_all[-1][-1]['timestamp'])    
      print(f'完成{len(data_all)}次')   
      
      if len(data_all[-1]) < 1000:
         break        







   shuju_dic = [data_all[i][j]  for i in range(0,len(data_all)) for j in range(0,len(data_all[i]))] #将所有数据改为一个个字典形式，存入shuju_dic列表


   shuju_dic_2 = []                                    
   for i in range(len(shuju_dic)):
      shuju_dic[i]['idd'] = int(shuju_dic[i]['id'].split('#')[1])    #将每个字典的id对应的value拆分为两部分，为每个字典增加一对键值对，为idd:~
      shuju_dic_2.append(shuju_dic[i])                             #将新的字典存入shuju_dic_2


   times_dic = {i['timestamp']: i for i in shuju_dic_2}     #构建时间戳与字典的映射,同时去除掉完全相同的数据

   for i in shuju_dic_2:
      k=i['timestamp']
      if k in times_dic.keys():
         if i['idd']>times_dic[k]['idd']:
               times_dic[k]=i
         
   shuju_notrepeat = [(k,v) for k,v in times_dic.items()]          #将字典形式变换为元组组成的列表 [(timestamp,{}), (), ()...]形式
   shuju_notrepeat.sort(key = lambda x:x[0])                       #将列表按照时间戳排序[(timestamp,{}), (), ()...]
   shuju_notrepeat = [i[1] for i in shuju_notrepeat]               #取列表中数组的第二个



   shuju_notrepeat = [i  for i in shuju_notrepeat if int(i['timestamp']) <time_end_timeStamp ]       #形式[{},{},{},{}],同时将超过的部分删除
      
   for i in shuju_notrepeat:
         i.pop('idd')
         
   change_rate=[0]                           #用于存储变化率，第一次交易的变化率设为0，从第2笔交易开始有变化率的概念。
   for i in range(1,len(shuju_notrepeat)):
      b_1=int(shuju_notrepeat[i-1]['tick'])         #第i-1次交易的tick
      b_2=int(shuju_notrepeat[i]['tick'])           #第i次的tick
      b_3=(1.0001**b_2-1.0001**b_1)/(1.0001**b_1)   #第i次交易相对第i-1次的变化率
      change_rate.append(b_3)

   change_rate_sum = 0              #将变化率的绝对值求和
   for i in range(len(change_rate)):
      change_rate_sum = change_rate_sum+abs(change_rate[i])

   change_rate_mean = change_rate_sum/(float(len(change_rate)-1))
   
#   shuju_notrepeat.reverse()
   
   
   change_rate_minute = change_rate_sum/(day*24*60)
   
   print(len(change_rate))
   print(day*24*60)
   return json.dumps({'绝对平均变化率':str( format(change_rate_mean *100,'.3f') )+'%','每分钟变化率': str( format(change_rate_minute *100,'.3f') )+'%'})



if __name__ == '__main__':
   app.run(debug=True, host="0.0.0.0",port=1919)

