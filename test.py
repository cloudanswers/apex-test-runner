import gevent
from gevent import monkey
monkey.patch_all()

import json
import os
import re
import requests
from simple_salesforce import Salesforce
import sys
from time import sleep


# env file functions derrived from honcho

def __parse_env(content):
    for line in content.splitlines():
        m1 = re.match(r'\A([A-Za-z_0-9]+)=(.*)\Z', line)
        if m1:
            key, val = m1.group(1), m1.group(2)
            # handle single quote enclosed value
            m2 = re.match(r"\A'(.*)'\Z", val)
            if m2:
                val = m2.group(1)
            # handle double quote enclosed value
            m3 = re.match(r'\A"(.*)"\Z', val)
            if m3:
                val = re.sub(r'\\(.)', r'\1', m3.group(1))
            os.environ[key] = val


def __read_env_file():
    if os.path.exists('.env'):
        try:
            with open('.env') as f:
                __parse_env(f.read())
        except IOError:
            # you don't have to have an env file
            pass


global sf


def _connect():
    global sf, base_url, headers
    # start one connection so everyone can use it
    sf = Salesforce(username=os.environ.get('USERNAME', ''),
                    password=os.environ.get('PASSWORD', ''),
                    security_token=os.environ.get('TOKEN', ''),
                    sandbox=os.environ.get('SANDBOX', '') != '')

    base_url = 'https://' + sf.sf_instance + \
               '/services/data/v28.0/sobjects/ApexTestQueueItem'
    headers = {"Authorization": "Bearer " + sf.session_id,
               'Content-type': 'application/json'}


def _queue_test(class_id):
    res = requests.post(base_url,
                        data=json.dumps({"ApexClassId": class_id}),
                        headers=headers)

    if 'Apex test class already enqueued' in res.content:
        print "%s is already scheduled for testing, sleeping..." % class_id
        print class_id
        print res.content
        sleep(10)
        return _queue_test(class_id)

    return res.json()['id']


def _query(soql):
    url = 'https://'+sf.sf_instance+'/services/data/v28.0/query/'
    params = {"q": soql}
    res = requests.get(url, headers=headers, params=params)
    assert res.status_code == 200
    return res.json()['records']


def _check_test_result(test_id):
    res = requests.get(base_url + '/' + test_id, headers=headers)
    res = res.json()
    if res['Status'] not in ('Queued', 'Processing'):
        assert res['Status'] == 'Completed', 'bad status: %s' % res['Status']
        items = res['ExtendedStatus'][1:-1].split('/')
        if items[0] != items[1]:
            print "ERROR"
            res2 = _query(("select MethodName, Message, StackTrace "
                          "from ApexTestResult "
                          "where Outcome != 'Pass' "
                          "and AsyncApexJobId = '%s'" % res['ParentJobId']))
            for r in res2:
                print "*" * 78
                print r['Message']
                print r['StackTrace']
                print "*" * 78
        print test_id, res['ExtendedStatus']
        return True


def _test(class_id):
    test_id = _queue_test(class_id)
    for i in range(30):
        gevent.sleep(i*10)
        if _check_test_result(test_id):
            return
    print "the test for class_id %s took too long, exiting" % class_id


def _last_apex_class_change():
    last_soql = ("select SystemModstamp from ApexClass "
                 "order by SystemModstamp desc limit 1")
    res = _query(last_soql)
    if res:
        return res[0]['SystemModstamp']


def _sleep_until_new_change(last, sleep_duration=2):
    for i in range(5):
        sleep(sleep_duration)
        new_last = _last_apex_class_change()
        if new_last != last:
            return new_last
    if sleep_duration < 100:
        _sleep_until_new_change(last, sleep_duration * 2)
    else:
        # about 5 mins
        print "No new tests for too long, shutting down to save api calls"
        exit(1)


def class_ids(pattern):
    soql = ("select Id, Name, SystemModstamp "
            "from ApexClass where Name like '%s'")
    for r in _query(soql % pattern):
        yield r['Id']


def _tests(pattern):
    return [gevent.spawn(_test, class_id) for class_id in class_ids(pattern)]


def process_forever(pattern):
    last = _last_apex_class_change()
    while True:
        gevent.joinall(_tests(pattern))
        last = _sleep_until_new_change(last)
        print "Change detected, running again...."


if __name__ == "__main__":
    __read_env_file()
    _connect()
    pattern = '%test%' if len(sys.argv) < 2 else sys.argv[1]
    print 'Running tests matching "%s"' % pattern
    process_forever(pattern)
