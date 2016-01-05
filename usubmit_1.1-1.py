#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
Copyright 2015, Luis Javier Gonzalez (luis.j.glez.devel@gmail.com)

This program is licensed under the GNU GPL 3.0 license.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import requests, json, getopt, sys, os

# INITIAL CHECK AND SETUP

BASE_PATH = os.getenv("HOME", "/usr/tmp")
if BASE_PATH == "/usr/tmp":
	print "Info: no user data is going to be used or saved for this session"
UTOOLS_PATH = "/.utools"
USUBMIT_PATH = "/usubmit"
LOGIN_DB = BASE_PATH + UTOOLS_PATH + USUBMIT_PATH + "/users.db"
try:
	f = open(LOGIN_DB,"a")
	f.write("\n")
	f.close()
except:
	try:
		os.makedirs(BASE_PATH + UTOOLS_PATH + USUBMIT_PATH)
	except:
		pass
	f = open(LOGIN_DB,"w")
	f.write("{}")
	f.close()

# DATA AND FUNCTIONS FOR DATA

HOST_URL = "https://uva.onlinejudge.org"
LOGIN_URL = "/index.php?option=com_comprofiler&task=login"
SUBMIT_URL = "/index.php?option=com_onlinejudge&Itemid=25&page=save_submission"

basic_header = {
	"Origin": "https://uva.onlinejudge.org",
	"Connection": "keep-alive",
	"Referer": "https://uva.onlinejudge.org/",
	"Accept-Charset": "utf-8,ISO-8859-1",
	"Accept-Language": "en-US,en;q=0.8",
	"User-Agent" : "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36",
	"Accept" : "text/html, application/xml, text/xml, */*"
}

send_header = {
	"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"
}

user_data = {
	"username":"",
	"passwd":""
}

const_login_data = {
	"op2":"login",
	"lang":"english",
	"force_session":"1",
	"message":"0",
	"loginfrom":"loginmodule",
	"remember":"yes",
	"Submit":"Login"
}

def var_login_data(html):
	var_login_data = { "return":"", "cbsecuritym3":"" }
	new = html[html.find('name="return" value="')+21:]
	var_login_data["return"] = new[:new.find('"')]
	new = html[html.find('name="cbsecuritym3" value="')+27:]
	var_login_data["cbsecuritym3"] = new[:new.find('"')]
	new = new[new.find("name=")+6:new.find('<input type="checkbox" name="remember" id="mod_login_remember"')]
	var_login_data[new[:new.find('"')]] = "1"
	return var_login_data

def number_from_filename(filename):
	num = ""
	beg = False
	for c in filename:
		if c.isdigit():
			num += c
			beg = True
		else:
			if beg == True:
				break
	try:
		num = int(num)
	except:
		print "Error: problem number not inferable from filename"
		exit(2)
	return num

def language_from_filename(filename):
	lang_dict = { ".c":1, ".cc":5, ".cpp":5, ".java":2, ".p":4, ".pas":4, ".pascal":4 }
	for suffix in lang_dict.keys():
		if filename.endswith(suffix):
			return lang_dict[suffix]
	print "Error: language not inferable from filename"
	exit(3)

# DATA FROM ARGUMENTS

save_login = False
prob_num = None
language = None

opts, args = getopt.getopt(sys.argv[1:], "u:sp:n:l:", ["username=", "save_login", "password=", "number=", "language="])
for o, a in opts:
	if o in ("-u","--username"):
		user_data["username"] = a
	if o in ("-s","--save_login"):
		save_login = True
	if o in ("-p","--password"):
		user_data["passwd"] = a
	if o in ("-n","--number"):
		prob_num = int(a)
	if o in ("-l","--language"):
		language = int(a)

if len(args) != 1: #1
	print "Error: incorrect order of arguments or number of files"
	exit(1)
prob_file = args[0]

if prob_num == None:
	prob_num = number_from_filename(prob_file) #2

if language == None:
	language = language_from_filename(prob_file) #3

if user_data["username"] == "":
	f = open (LOGIN_DB)
	_data = json.load(f)
	f.close()
	if len(_data) != 1: #4
		print "Error: username not specified"
		exit(4)
	user_data["username"] = _data.keys()[0]
	user_data["passwd"] = _data.values()[0]

if user_data["passwd"] == "":
	f = open (LOGIN_DB)
	_data = json.load(f)
	f.close()
	try:
		passwd = _data[user_data["username"]]
	except:
		print "Info: username not in database"
		passwd = raw_input("Password for %s: " % user_data["username"])
	user_data["passwd"] = passwd

if save_login:
	f = open (LOGIN_DB)
	_data = json.load(f)
	f.close()
	_data[user_data["username"]] = user_data["passwd"]
	f = open (LOGIN_DB,"w")
	f.write(json.dumps(_data))
	f.close()

# LOGIN

try:
	S = requests.Session()
	r = S.get(HOST_URL, headers = basic_header, stream = True)
except:
	print "Error: no network connection" #7
	exit(7)

composed = {}
composed.update(user_data)

composed.update(const_login_data)
composed.update(var_login_data(r.text))

try:
	r = S.post(HOST_URL + LOGIN_URL, data = composed, headers = send_header, stream = True)
except:
	print "Error: no network connection" #7
	exit(7)

if r.text.find("Logout")>0:
	print "Login [Done]"
else:
	print "Login [Error]" #5
	exit(5)

# SUBMIT

try:
	f = open(prob_file)
	prob_data = { "localid": str(prob_num), "code": f.read(), "language": str(language), "problemid":"", "category": "", "codeupl": ""}
	f.close()
except:
	print "Error: source file %s not found" % prob_file #8
	exit(8)

print "Submission:\n\tproblem # %d" % prob_num
print "\tlanguage # %d" % language,
if language == 1:
	print "(ANSI C)"
if language == 2:
	print "(JAVA)"
if language == 3:
	print "(C++)"
if language == 4:
	print "(PASCAL)"
if language == 5:
	print "(C++11)"
print "\tsource file %s" % prob_file
print "\tuser %s" % user_data["username"]
ans = "k"
while ans != "y" and ans != "n":
	ans = raw_input("Submit? (Y/n) ")
	ans.lower()
	if ans == "":
		ans = "y"
	if ans == "n":
		print "Info: exiting without sending"
		exit(-1)

try:
	r = S.post(HOST_URL + SUBMIT_URL, data = prob_data, stream = True)
except:
	print "Error: no network connection" #7
	exit(7)

if r.text.find("Submission+received+with+ID+")>0:
	print "Sending [Done]"
else:
	print "Sending [Error]" #6
	exit(6)
