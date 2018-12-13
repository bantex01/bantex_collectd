#!/usr/bin/python
 
import collectd
import os
import filecmp
import re
import subprocess
import sys
import json
import time
from collections import defaultdict
 
#####################################################################
# Gloabl VARS
#####################################################################
 
RUN_DIR = os.path.dirname(os.path.join(os.getcwd(), __file__))
COLLECTD_CFG = defaultdict(dict)
CONFIGS = []
 
#####################################################################
# Functions
#####################################################################
 
def parse_conf(conf_file):
 
        conf_file = RUN_DIR + "/../etc/" + conf_file
        if (os.path.exists(conf_file)):
                conf_file = open(conf_file,'r')
                for conf_line in conf_file:
 
                        if (re.match(r'^\[(.*)\]',conf_line)):
                                stanza_cfg=re.search(r'^\[(.*)\]',conf_line)
                                stanza=stanza_cfg.group(1)
                                continue
 
                        if (re.match(r'search.?=.?\'(.*)\'',conf_line)):
                                cfg_items=re.search(r'search.?=.?\'(.*)\'',conf_line)
                                COLLECTD_CFG[stanza]['search'] = cfg_items.group(1)
                                continue
 
                        if (re.match(r'\w+.*=.?.+',conf_line)):
                                cfg_items=re.search(r'(\w+).*=.?(.+)',conf_line)
                                COLLECTD_CFG[stanza][cfg_items.group(1)] = cfg_items.group(2)
                                continue
 
        else:
        collectd.error("splunk_search plugin: configuration parsing has failed, no conf file found - " +str(conf_file))
 
 
def run_search(search_stanza):
 
    try:
 
        search = str(COLLECTD_CFG[search_stanza]['search'])
        curl_cmd = "/usr/bin/curl -m " + COLLECTD_CFG[search_stanza]['timeout'] + " -k -s -u admin:iLAiitQjixlrsPPNwXI8nyxgmumraH " + "-d \"exec_mode=" + COLLECTD_CFG[search_stanza]['exec_mode'] + "\"" + " -d \"search=" + COLLECTD_CFG[search_stanza]['search'] + "\"" + " -d \"earliest_time=" + COLLECTD_CFG[search_stanza]['earliest_time'] + "\""  + " -d \"latest_time=" + COLLECTD_CFG[search_stanza]['latest_time'] + "\"" + " -d \"output_mode=json" + "\"" + " https://localhost:8089/services/search/jobs"
        start = time.time()
        out = subprocess.check_output([curl_cmd], shell=True, stderr=subprocess.STDOUT)
        end = time.time()
        data = json.loads(out)
        dur = end-start
        return dur
 
 
    except Exception, e:
        f = open("/tmp/collectd_splunk_search.err", "a")
        f.write(str(time.time()) + " - splunk_search - run_search has failed for "+ str(curl_cmd) + " , exception: " +str(e) + "\n")
        return 0
 
 
def config_func(config):
 
    search_set = False
    for node in config.children:
        key = node.key.lower()
        val = node.values[0]
        if key == 'search':
            global SEARCH
            SEARCH = val
            search_set = True
            collectd.info("search set "+str(SEARCH))
            continue
 
        elif key == 'key':
            global KEY
            KEY = val
            continue
 
        else:
            collectd.info('splunk_search plugin: Unknown config key "%s"' % key)
 
    if search_set:
        collectd.info('splunk search plugin: Using search %s' % SEARCH)
    else:
        collectd.info('splunk search plugin: Using default search %s' % SEARCH)
        global SEARCH
        SEARCH = "default"
        search_set = True
 
    CONFIGS.append({
        'SEARCH': SEARCH,
        'KEY': KEY,
    })
 
 
def read_func():
 
    for conf in CONFIGS:
        val = collectd.Values(type='latency')
        val.type_instance = conf['KEY']
        val.plugin = 'splunk_search'
        search_time = run_search(conf['SEARCH'])
        val.dispatch(values=[search_time])
 
 
#####################################################################
# Main
#####################################################################
 
parse_conf('splunk_search.conf')
collectd.register_config(config_func)
collectd.register_read(read_func)
