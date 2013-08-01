import gevent
from gevent import monkey
monkey.patch_all(httplib=True)

import json
import requests
from requests.auth import HTTPBasicAuth
from simple_salesforce import Salesforce
import sys
from time import sleep


# start one connection so everyone can use it
sf = Salesforce(username='',
			    password='',
                security_token='',
                sandbox=True)

base_url = 'https://'+sf.sf_instance+\
           '/services/data/v28.0/sobjects/ApexTestQueueItem'
headers = {"Authorization": "Bearer "+sf.session_id,
           'Content-type': 'application/json'}

def _queue_test(class_id):
    res = requests.post(base_url, data=json.dumps({"ApexClassId": class_id}),
        headers=headers)
    if 'Apex test class already enqueued' in res.content:
        print "You probably have 10 copies of each test scheduled"
        exit(1)
    return res.json()['id']

def _query(soql):
    url = 'https://'+sf.sf_instance+'/services/data/v28.0/query/'
    params = {"q": soql}
    res = requests.get(url, headers=headers, params=params)
    return res.json()['records']

def _check_test_result(test_id):
    res = requests.get(base_url + '/' + test_id, headers=headers)
    res = res.json()
    if res['Status'] not in ('Queued', 'Processing'):
        assert res['Status'] == 'Completed', 'bad status: %s' % res['Status']
        items = res['ExtendedStatus'][1:-1].split('/')
        if items[0] != items[1]:
            print "ERROR"
            res = _query(("select MethodName, Message, StackTrace "
                          "from ApexTestResult "
                          "where Outcome != 'Pass' "
                          "and AsyncApexJobId = '%s'" % res['ParentJobId']))
            for r in res:
                print "*" * 78
                print r['Message']
                print r['StackTrace']
                print "*" * 78                
            # exit(1)
        print test_id, "ok"
        return True

def test(class_id):
    test_id = _queue_test(class_id)
    sleep_times = 0
    while True:
        if _check_test_result(test_id):
            break
        gevent.sleep(3)
        sleep_times += 1
        if sleep_times > 10:
            gevent.sleep(3)
        assert sleep_times < 20, "%s slept too many times" % class_id

def class_ids(pattern):
    for r in _query("select Id, Name from ApexClass where Name like '%s'" % pattern):
        yield r['Id']

if __name__ == "__main__":
    pattern = '%test%' if len(sys.argv) < 2 else sys.argv[1]
    print 'Running tests matching "%s"' % pattern
    threads = []
    for class_id in class_ids(pattern):
        threads.append(gevent.spawn(test, class_id))
    gevent.joinall(threads)
