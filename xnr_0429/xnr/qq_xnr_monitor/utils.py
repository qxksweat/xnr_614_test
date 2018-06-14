# -*- coding: utf-8 -*-
'''
use to save function---about deal database
'''
import sys
import json
import datetime
from xnr.global_utils import es_xnr,qq_xnr_index_name,qq_xnr_index_type,\
                             group_message_index_name_pre, group_message_index_type
from global_utils import qq_report_management_index_name,qq_report_management_index_type
from xnr.parameter import MAX_VALUE, DAY, group_message_windowsize
from xnr.time_utils import get_groupmessage_index_list,ts2datetime,datetime2ts,ts2date,date2ts


def aggr_sen_users(xnr_qq_number, startdate ,enddate):
    # print 'startdate:',startdate,type(startdate)
    start_ts = datetime2ts(startdate)
    end_ts = datetime2ts(enddate)
    query_body = {
        "query":{
                    "bool":{
                        "must":[
                            {'term':{'xnr_qq_number': xnr_qq_number}},
                            {"term":{"sensitive_flag":1}},
                            {'range':{'timestamp':{'gte': start_ts, 'lt':end_ts}}}

                        ]
                    }
        },
        "aggs":{
            "all_senusers":{
                # "terms":{"field": "speaker_qq_number"}
                "terms":{"field": "speaker_nickname"}
            }
        }
    }


    #enddate = datetime.datetime.now().strftime('%Y-%m-%d')
    #startdate = ts2datetime(datetime2ts(enddate)-group_message_windowsize*DAY)
    index_names = get_groupmessage_index_list(startdate,enddate)
    
    print index_names
    results = []
    for index_name in index_names:    
        try:
            result = es_xnr.search(index=index_name,\
                    doc_type=group_message_index_type,\
                    body=query_body)["aggregations"]["all_senusers"]["buckets"]
        except Exception,e:
            result = []
        print 'index_name,result:', index_name, result

        if result != []:
            for item in result:
                # print 'item:',item
                inner_item = {}
                # inner_item['qq_number'] = item['key']
                inner_item['qq_nick'] = item['key']
                inner_item['count'] = item['doc_count']
                info = get_speaker_info(item['key'],index_name)
                if info == {}:
                    # inner_item['qq_nick'] = ''
                    inner_item['qq_number'] = ''
                    inner_item['qq_groups']=''
                    inner_item['last_speak_ts'] = ''
                    inner_item['text'] = []
                else:
                    # inner_item['qq_nick'] = info['qq_nick']
                    inner_item['qq_number'] = info['qq_number']
                    inner_item['qq_groups']=info['qq_groups']
                    inner_item['last_speak_ts'] = info['last_speak_ts']
                    inner_item['text'] = info['text']
                flag = 1
                for aa in results:                              #检验是否已经在结果中
                    # if aa['qq_number'] == inner_item['qq_number']:
                    if aa['qq_nick'] == inner_item['qq_nick']:
                        aa['count'] += inner_item['count']
                        aa['last_speak_ts'] = inner_item['last_speak_ts']
                        aa['qq_groups'].update(inner_item['qq_groups'])     # 多个群发言的更新
                        aa['text'].extend(inner_item['text'])
                        flag = 0
                        continue
                if flag:        
                    results.append(inner_item)
                
    return results


def get_speaker_info(qq_nick,index_name):
    print 'qq_nick:',qq_nick
    query_body = {
        "query": {
            "filtered":{
                "filter":{
                    "bool":{
                        "must":[
                            {"term":{"speaker_nickname":qq_nick}},
                            {"term":{"sensitive_flag":1}}
                        ]
                    }
                }
            }
            },
            "size": MAX_VALUE,
            "sort":{"timestamp":{"order":"desc"}}
        }

    result = es_xnr.search(index=index_name, doc_type=group_message_index_type, body=query_body)['hits']['hits']
    results = {}
    # print 'result:',result
    source = result[0]['_source']
    if source != []:
        results['qq_nick'] = source['speaker_nickname']
        results['qq_number'] = source['speaker_qq_number']
        results['last_speak_ts'] = source['timestamp']
        results['qq_groups'] = {source['qq_group_number']:source['qq_group_nickname']}
    for item in result:
        source = item['_source']
        text_item = [source['text'], source['timestamp'], source['sensitive_words_string']]
        #print 'text_item:', text_item
        try:
            results['text'].append(text_item)
        except:
            results['text'] = [text_item]
    #print 'final results:', results
    return results



def rank_sen_users(users):
    result = sorted(users.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    # print result
    return result

def search_by_xnr_number(xnr_qq_number, current_date):
    # 用于显示操作页面初始的所有群历史信息
    query_body = {
        "query": {
            "filtered":{
                "filter":{
                    "bool":{
                        "must":[
                            {"term":{"xnr_qq_number":xnr_qq_number},
                            "term":{"sensitive_flag":1}
                            }

                        ]
                    }
                }
            }
            },
            "size": MAX_VALUE,
            "sort":{"sensitive_value":{"order":"desc"}}
        }

    enddate = current_date
    startdate = ts2datetime(datetime2ts(enddate)-group_message_windowsize*DAY)
    index_names = get_groupmessage_index_list(startdate,enddate)
    # print index_names
    results = []
    for index_name in index_names:
        # if not es_xnr.indices.exsits(index=index_name):
        #     continue
        try:
            result = es_xnr.search(index=index_name, doc_type=group_message_index_type,body=query_body)['hits']['hits']
            # if results != {}:
            #     results['hits']['hits'].extend(result['hits']['hits'])
            # else:
            #     results=result.copy()
            if result:
                for item in result:
                    item['_source']['_id'] = item['_id']
                    results.append(item['_source'])
            else:
                pass
        except:
            pass
    # print 'results:',results
    return results


def search_by_period(xnr_qq_number,startdate,enddate):
    results = []
    query_body = {
        "query": {
            "filtered":{
                "filter":{
                    "bool":{
                        "must":[
                            {"term":{"xnr_qq_number":xnr_qq_number},
                            "term":{"sensitive_flag":1}
                            }

                        ]
                    }
                }
            }
            },
            "size": MAX_VALUE,
            "sort":{"timestamp":{"order":"desc"}}
    }
    # es.search(index=”flow_text_2013-09-02”, doc_type=”text”, body=query_body)

    index_names = get_groupmessage_index_list(startdate,enddate)
    for index_name in index_names:
        # if not es_xnr.indices.exsits(index_name):
        #     continue
        try:
            result = es_xnr.search(index=index_name, doc_type=group_message_index_type,body=query_body)['hits']['hits']
            # if results != {}:
            #     results['hits']['hits'].extend(result['hits']['hits'])
            # else:
            #     results=result.copy()
            if result:
                for item in result:
                    item['_source']['_id'] = item['_id']
                    results.append(item['_source'])
            else:
                pass
        except:
            pass
    # if results == {}:
    #     results={'hits':{'hits':[]}}
    return results


def report_warming_content(report_type, report_time, xnr_user_no,\
               qq_number, qq_content_info):
    report_dict = dict()
    report_dict['report_type'] = report_type
    report_dict['report_time'] = int(report_time)
    report_dict['xnr_user_no'] = xnr_user_no
    report_dict['qq_number'] = qq_number
    report_dict['qq_nick'] = ''
    report_dict['report_content'] = json.dumps(qq_content_info)
    report_id = xnr_user_no + '_' + str(report_time)
    try:
        es_xnr.index(index=qq_report_management_index_name, \
            doc_type=qq_report_management_index_type, id=report_id,\
            body=report_dict)
        mark = True
    except:
        mark = False
    return mark


def get_user_text(qq_nick,qq_groups,last_speak_ts):
    print 'qq_nick:',qq_nick
    query_body = {
        "query": {
            "filtered":{
                "filter":{
                    "bool":{
                        "must":[
                            {"term":{"speaker_nickname":qq_nick}},
                            {"term":{"sensitive_flag":1}},
                            {"term":{"qq_group_nickname":qq_groups}}
                        ]
                    }
                }
            }
            },
            "size": MAX_VALUE,
            "sort":{"timestamp":{"order":"desc"}}
        }
    index_name = group_message_index_name_pre + ts2datetime(last_speak_ts)
    result = es_xnr.search(index=index_name, doc_type=group_message_index_type, body=query_body)['hits']['hits']
    results = {}

    for item in result:
        source = item['_source']
        text_item = [source['text'], source['timestamp'], source['sensitive_words_string']]
        #print 'text_item:', text_item
        try:
            results['text'].append(text_item)
        except:
            results['text'] = [text_item]
    #print 'final results:', results
    return results


def report_warming_content_new(task_detail):
    report_dict = dict()
    report_dict['report_type'] = task_detail['report_type']
    report_dict['report_time'] = task_detail['report_time']
    report_dict['xnr_user_no'] = task_detail['xnr_user_no']
    report_dict['qq_number'] = task_detail['qq_number'] 
    report_dict['qq_nickname'] = task_detail['qq_nickname']


    if task_detail['report_type'] == '人物':
    	user_info = []
        for item in task_detail['user_info']:
            qq_groups = item['qq_groups'].values()
            item['text'] = get_user_text(item['qq_nick'],qq_groups,item['last_speak_ts'])
            user_info.append(item)
        report_id = task_detail['xnr_user_no'] + '_' + task_detail['qq_nickname']
        report_dict['report_content'] = json.dumps(user_info)

    elif task_detail['report_type'] == '言论':
        report_id = task_detail['report_id']
        report_content = []
        for item in task_detail['content_info']:
            index_name = group_message_index_name_pre + ts2datetime(int(item['timestamp']))
            try:
                content_result=es_xnr.get(index=index_name,doc_type=group_message_index_type,id=item['_id'])['_source']
                #print 'content_result:',content_result,type(content_result)
                report_content.append(content_result)
            except:
                print 'content error!'
        report_dict['report_content'] = json.dumps(report_content)

    try:
        es_xnr.index(index=qq_report_management_index_name, \
            doc_type=qq_report_management_index_type, id=report_id,\
            body=report_dict)
        mark = True
    except:
        mark = False
    return mark
