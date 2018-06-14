#-*- coding:utf-8 -*-
import os
import time
import datetime
import json
from flask import Blueprint,url_for,render_template,request,\
        abort,flash,session,redirect

#from xnr.global_utils import 
from utils import show_report_content,output_excel_word

mod=Blueprint('qq_xnr_report_manage',__name__,url_prefix='/qq_xnr_report_manage')

@mod.route('/show_report_content/')
def ajax_show_report_content():
    report_type = request.args.get('report_type', '').split(',')
    start_ts = request.args.get('start_ts', '')
    end_ts = request.args.get('end_ts', '')
    qq_xnr_no = request.args.get('qq_xnr_no', '')
    #test
    '''
    report_type = 'content'
    start_ts = 1506584253 - 3600*24
    end_ts = 1506584253 + 3600*24
    qq_xnr_no = 'QXNR0003'
    '''
    result = show_report_content(report_type, start_ts, end_ts, qq_xnr_no)
    return json.dumps(result)

@mod.route('/output_excel_word/') 
def ajax_output_excel_word():
    id_list=request.args.get('id_list','').split(',')
    out_type=request.args.get('out_type','')
    # report_timelist=request.args.get('report_timelist','').split(',')
    results=output_excel_word(id_list,out_type,report_timelist)
    return json.dumps(results)
