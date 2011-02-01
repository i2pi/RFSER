import web
import psycopg2
import psycopg2.extras
import random
import string
import json

from distutils.dir_util import mkpath

import pprint

urls = ('/', 'Index',
		'/report/(.*)/receipts', 'ReportReceipts',
		'/report/(.*)/details', 'ReportDetails',
		'/report/(.*)/reimburse', 'ReportReimburse',
		'/report/(.*)', 'Report',
		'/receipt/image', 'ReceiptImage',
		'/receipt/(.*)/image', 'ReceiptImage',
		'/receipt/(.*)/details', 'ReceiptDetails',
		'/collection/(.*)/add/(.*)', 'CollectionAdd',
		'/collection/(.*)', 'Collection')

IMG_PATH = 'images/'

def get_db_conn():
	return psycopg2.connect(database='rfser', host='localhost', user='rfser', password='B3zhD9K39:,iq846TjAM%Wz')


def gen_new_id(conn, table):
	new_id = ''.join(random.choice(string.ascii_letters) for x in range(10))
	cur = conn.cursor()
	sql = "INSERT INTO %s (%s_id) " % (table, table) + 'VALUES (%(new_id)s)';
	try:
		cur.execute(sql, {'new_id': new_id})
		conn.commit();
	except psycopg2.IntegrityError:
		conn.commit();
		new_id = gen_new_id(conn, table)
	cur.close()
	return new_id

class Index:
	def GET(self):
		conn = get_db_conn()
		new_id = gen_new_id(conn, 'report')
		conn.close()
		raise web.seeother('/report/' + new_id)


class Report:
	def GET(self, report_id):
		if len(report_id) < 3:
			conn = get_db_conn()
			new_id = gen_new_id(conn, 'report')
			conn.close()
			raise web.seeother('/report/' + new_id)
		return open('index.html').read()

	def POST(self, report_id):
		data = web.input()
		data['report_id'] = report_id;

		if 'reportName' not in data.keys():
			return web.badrequest()
		if 'employee' not in data.keys():
			return web.badrequest()
		if len(data['reportName']) < 3:
			return web.badrequest()
		if len(data['employee']) < 2:
			return web.badrequest('Employee name too short')

		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""UPDATE report
		               SET name=%(reportName)s, employee=%(employee)s, submitted=now() 
		               WHERE report_id = %(report_id)s""", data)
		conn.commit()
		conn.close()
		return "OK"

class ReportDetails:
	def GET(self, report_id):
		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""SELECT name, employee, COALESCE(TO_CHAR(reimbursed, 'Mon D, YYYY HH:MMam'), 'No') 
		               FROM report WHERE report_id = %(report_id)s""", {'report_id': report_id});
		rows = cur.fetchall()
		if len(rows) != 1:
			return web.notfound()
		row = rows[0]

		reportName = row[0]
		if reportName is None:
			reportName = ''
		employee = row[1]
		if employee is None:
			employee = ''

		conn.close()

		return "[{reportName: \"%s\", employee: \"%s\", reimbursed: \"%s\"}]" % (reportName, employee, row[2]);

class ReportReimburse:
	def POST(self, report_id):
		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""UPDATE report SET reimbursed = now() WHERE reimbursed IS NULL AND report_id=%(report_id)s""", {'report_id': report_id});
		conn.commit()
		conn.close()
		
		return "OK"

class ReportReceipts:
	def GET(self, report_id):
		conn = get_db_conn()
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute("""SELECT receipt_id, COALESCE(amount,0), COALESCE(description, '')
		               FROM receipt WHERE report_id = %(report_id)s""",
		            {'report_id': report_id})
	
		rows = cur.fetchall();
		jrow = []
		for r in rows:
			jrow.append('{receipt_id: \"%s\", amount: %s, description: \"%s\"}' % (r[0], r[1], r[2]))

		conn.close()

		return '[' + ','.join(jrow) + ']'

class ReceiptImage:
	def POST(self):
		data = web.input()
		if 'receipt' in data.keys():
			img = data['receipt']
		else:
			return web.badrequest()

		referer = web.ctx.env.get('HTTP_REFERER')
		report_id = referer.split('/')[::-1][0]
	
		conn = get_db_conn()		
		cur = conn.cursor()
		cur.execute("""SELECT * FROM report WHERE report_id = %(report_id)s AND submitted IS NULL""",
		            {'report_id': report_id})
		rows = cur.fetchall()
		if len(rows) != 1:
			conn.close()
			return web.forbidden("Can't alter a report that has already been submitted");

		receipt_id = gen_new_id(conn, 'receipt')

		cur = conn.cursor()
		cur.execute("""UPDATE receipt SET report_id = %(report_id)s WHERE receipt_id = %(receipt_id)s""",
		            {'report_id': report_id, 'receipt_id': receipt_id})
		conn.commit()
		conn.close()

		path = IMG_PATH + receipt_id[0] + '/' + receipt_id[1] + '/'
		mkpath(path)
		fp = open(path + receipt_id + "_original", 'w')
		fp.write(img)
		fp.close()

		return '{"receipt_id" : \"%s\"}' % receipt_id

	def GET(self, receipt_id):
		if len(receipt_id) < 4:
			return web.badrequest()
		path = IMG_PATH + receipt_id[0] + '/' + receipt_id[1] + '/'
		fp = open(path + receipt_id + "_original")
		img = fp.read()
		fp.close()
		return img

class ReceiptDetails:
	def POST(self, receipt_id):
		if len(receipt_id) < 4:
			return web.badrequest()

		referer = web.ctx.env.get('HTTP_REFERER')
		report_id = referer.split('/')[::-1][0]

		if len(report_id) < 4:
			return web.badrequest()

		data = web.input()

		data['receipt_id'] = receipt_id
		data['report_id'] = report_id

		if 'amount' not in data.keys():
			return web.badrequest()

		if 'description' not in data.keys():
			return web.badrequest()

		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""UPDATE receipt 
		               SET amount=%(amount)s, description = %(description)s 
		               WHERE receipt_id = %(receipt_id)s AND report_id = %(report_id)s""", data)
		conn.commit()
		conn.close()

		return "OK"

class Collection:
	def GET(self, collection_id):
		if len(collection_id) == 0:
			conn = get_db_conn()
			new_id = gen_new_id(conn, 'collection')
			conn.close()
			raise web.seeother('/collection/' + new_id)
		return collection_id

class CollectionAdd:
	def POST(self, collection_id, report_id):
		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""INSERT INTO collection_report (collection_id, report_id) 
		               VALUES (%(collection_id)s, %(report_id)s)""", {'collection_id': collection_id,
		               'report_id': report_id})
		conn.commit()
		conn.close()
		return "OK"

if __name__ == "__main__":
	app = web.application(urls, globals(), autoreload=True) 
	app.run()

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()


