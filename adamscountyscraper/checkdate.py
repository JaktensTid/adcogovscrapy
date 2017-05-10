
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://')
db = client['adcogov']
col = db['adcogovrecords']

dates = [datetime.strptime(d['recordDate'], '%m/%d/%Y %I:%M:%S %p') for d in col.find({},{'recordDate' : 1})]
#instr = set([d['instrument'] for d in col.find({},{'instrument' : 1})])
#print(len(list(instr)))
print(min(dates))



