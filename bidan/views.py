from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from polls.models import Question
from django.core.urlresolvers import reverse
from django.views import generic
import urllib2, base64, json
import socket
import xlwt
import json
import inflection
import sys
from datetime import datetime 
from .models import Response

# set timeout
# timeout in seconds
timeout = 10000
socket.setdefaulttimeout(timeout)

URL = "http://118.91.130.18:9979"
USERLOGIN = "user12"
PASSWORDLOGIN = "Satu2345"

USERGROUP1 = ['user1', 'user2', 'user3', 'user4', 'user5', 'user6', 'user8']
USERGROUP2 = ['user9', 'user10', 'user11', 'user12', 'user13', 'user14']
bindTypesId = {'kartu_ibu': 'kiId', 'ibu': 'motherId', 'anak': 'childId'}

# set xls style
style0 = xlwt.easyxf('font: name Times New Roman, color-index red, bold on; borders: top medium, bottom medium, left medium, right medium;',
    num_format_str='#,##0.00')

style1= xlwt.easyxf('font: name Times New Roman, color-index black, bold off; borders: top thin, bottom thin, left thin, right thin;',
    num_format_str='#,##0.00')


def get_width(num_characters):
    return int((1+num_characters) * 256)


def index(request):
	context = {'title' : "Hello World", 'users1' : USERGROUP1, 'users2' : USERGROUP2}
	return render(request, 'bidan/index.html', context)


def result(request, response_id):
	pieces = response_id.split('/')
	xlsfile = []
	sumxlsfile = ""
	for piece in pieces:
		response = get_object_or_404(Response, pk=piece)
		xlsfile.append(response)
		sumxlsfile += str(response.id) + "/"

	sumxlsfile = sumxlsfile[:-1]
	context = {'xlsfile' : xlsfile, 'sumxlsfile' : sumxlsfile, 'users1' : USERGROUP1, 'users2' : USERGROUP2 }
	return render(request, 'bidan/index.html', context)


def result_all(request, response_id):
	xlsfile = get_object_or_404(Response, pk=response_id)
	context = {'allxlsfile' : xlsfile, 'users1' : USERGROUP1, 'users2' : USERGROUP2 }
	return render(request, 'bidan/index.html', context)


def download_all(request, responses_id):
	wb = xlwt.Workbook()
	allform = {}
	userid = responses_id.split("/")
	xlsfile = []

	for uid in userid:
		_object = get_object_or_404(Response, pk=uid)
		xlsfile.append(_object)
		result_json = json.loads(_object.response_text)
		for row in result_json:
			if not row["formName"] in allform:
				allform[row["formName"]] = []
			jsondata = (json.loads(row["formInstance"]))
			jsonfield = list()
			jsonfield.append({'name': "UserID", 'value': row["anmId"]})
			jsonfield.append({'name': bindTypesId.get(jsondata["form"]["bind_type"], "none"), 'value': row["entityId"]})
			jsonfield.extend(jsondata["form"]["fields"])
			jsonfield.append({'name': "clientVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["clientVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
			jsonfield.append({'name': "serverVersionSubmissionDate", 'value' : datetime.fromtimestamp(int(row["serverVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
			allform[row["formName"]].append(jsonfield)

	for sheet in allform:
		# create worksheet
		worksheetTitle = sheet[0:30]
		wa = wb.add_sheet(inflection.humanize(worksheetTitle))
		titleArray = []
		formData = []
		
		# put the json data to array
		for idx1, data1 in enumerate(allform[sheet]):
			formData.append([])
			formData[idx1] = {}
			for idx2, data2 in enumerate(data1):
				if data2['name'] != 'id':
					if not data2['name'] in titleArray:
						titleArray.insert(idx2, data2['name'])
					value = data2.get('value')
					if value is None:
						value = '-'
					formData[idx1][data2['name']] = value

		# write al data to worksheet
		for idx1, data1 in enumerate(formData):
			for idx2, data2 in enumerate(titleArray):
				if idx1 == 0:
					wa.write(0, idx2, data2, style0)
				if data2 in data1:
					value = data1[data2]
					wa.col(idx2).width = get_width(len(value)) if get_width(len(value)) > wa.col(idx2).width else wa.col(idx2).width
					wa.write(idx1+1, idx2, inflection.humanize(value), style1)
				else:
					wa.write(idx1+1, idx2, '-', style1)

	xlsname = ""
	for xls in xlsfile :
		xlsname += xls.response_username + "+"
	xlsname = xlsname[:-1]
	xlsname += ".xls"

	return xls_to_response(wb, xlsname)	


def download(request, response_id):
	wb = xlwt.Workbook()
	xlsfile = get_object_or_404(Response, pk=response_id)
	result_json = json.loads(xlsfile.response_text)
	return create_xls(result_json, xlsfile, wb)


def auth(request):
	## get data from bidan here
	username = request.POST["username"]
	batch_size = request.POST["batch_size"]
	batch_size_string = ""
	if batch_size :
		batch_size_string = "&batch-size="+batch_size
	resobj = list()
	list_users = list()
	list_users.extend(request.POST.getlist('users[]'))

	if username.strip():
		list_users.append(username)

	if not list_users:
		return render(request, 'bidan/index.html', {'error_message' : "No user selected", 'users1' : USERGROUP1, 'users2' : USERGROUP2 })

	for user in list_users:
		API_URL = URL + "/form-submissions?anm-id="+user+"&timestamp=0"+batch_size_string
		print(API_URL)
		try:
			req = urllib2.Request(API_URL)
			base64String = base64.encodestring('%s:%s' % (USERLOGIN, PASSWORDLOGIN)).replace('\n', '')
			req.add_header("Authorization", "Basic %s" % base64String)
			result = urllib2.urlopen(req)
			result_json = json.load(result.fp)
			result.close()
			response = Response.objects.update_or_create(response_username=user,defaults=dict(response_text=json.dumps(result_json),response_password=PASSWORDLOGIN))
			resobj.append(response)
		except (socket.timeout, urllib2.HTTPError) as e:
			# return HttpResponse("Error: %s" % e)
			# Redisplay the question voting form.
			return render(request, 'bidan/index.html', {'error_message' : e, 'users1' : USERGROUP1, 'users2' : USERGROUP2 })

	arguments = ""
	for obj in resobj :
		arguments+=str(obj[0].id) + "/"
	arguments = arguments[:-1]

	return HttpResponseRedirect(reverse('bidan:result', args=(arguments,)))


def xls_to_response(xls, fname):
    response = HttpResponse(content_type="application/ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    xls.save(response)
    return response


def get_all(request):
	batchSize = request.POST["batch_size"]
	username = "demo1"
	password = "1"
	API_URL = URL + "/all-form-submissions?timestamp=0&batch-size="+batchSize
	try:
		req = urllib2.Request(API_URL)
		base64String = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
		req.add_header("Authorization", "Basic %s" % base64String)
		result = urllib2.urlopen(req)
		result_json = json.load(result.fp)
		result.close()
		resobj = Response.objects.update_or_create(response_username="all",defaults=dict(response_text=json.dumps(result_json),response_password=password))
		return HttpResponseRedirect(reverse('bidan:result_all', args=(resobj[0].id,)))
	except (socket.timeout, urllib2.HTTPError) as e:
		# return HttpResponse("Error: %s" % e)
		# Redisplay the question voting form.
		return render(request, 'bidan/index.html', {'error_message' : e, 'users1' : USERGROUP1, 'users2' : USERGROUP2 })


def create_xls(result_json, xlsfile, wb):
	all_form = {}

	for row in result_json:
		if not row["formName"] in all_form:
			all_form[row["formName"]] = []
		jsondata = (json.loads(row["formInstance"]))
		jsonfield = list()
		jsonfield.append({'name': "UserID", 'value': row["anmId"]})
		jsonfield.append({'name': bindTypesId.get(jsondata["form"]["bind_type"], "none"), 'value': row["entityId"]})
		jsonfield.extend(jsondata["form"]["fields"])
		jsonfield.append({'name': "clientVersionSubmissionDate", 'value': datetime.fromtimestamp(int(row["clientVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
		jsonfield.append({'name': "serverVersionSubmissionDate", 'value': datetime.fromtimestamp(int(row["serverVersion"])/1000.0).strftime('%Y-%m-%d %H:%M:%S')})
		all_form[row["formName"]].append(jsonfield)

	for sheet in all_form:
		# create worksheet
		worksheet_title = sheet[0:30]
		wa = wb.add_sheet(inflection.humanize(worksheet_title))
		title_array = []
		form_data = []

		# put the json data to array
		for idx1, data1 in enumerate(all_form[sheet]):
			form_data.append([])
			form_data[idx1] = {}
			for idx2, data2 in enumerate(data1):
				if data2['name'] != 'id':
					if not data2['name'] in title_array:
						title_array.insert(idx2, data2['name'])
					value = data2.get('value')
					if value is None:
						value = '-'
					form_data[idx1][data2['name']] = value

		# write al data to worksheet
		for idx1, data1 in enumerate(form_data):
			for idx2, data2 in enumerate(title_array):
				if idx1 == 0:
					wa.write(0, idx2, data2, style0)
				if data2 in data1:
					value = data1[data2]
					wa.col(idx2).width = get_width(len(value)) if get_width(len(value)) > wa.col(idx2).width else wa.col(idx2).width
					wa.write(idx1+1, idx2, value, style1)
				else:
					wa.write(idx1+1, idx2, '-', style1)

	return xls_to_response(wb, xlsfile.response_username+'.xls')

