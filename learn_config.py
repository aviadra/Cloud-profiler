#!/usr/local/bin/python
# coding: UTF-8

import configparser
config = configparser.ConfigParser()
config.read('/Users/aviad/.aws/credentials')
config.sections()
for i in config.sections(): 
    print(i) 