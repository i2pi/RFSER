import web
import psycopg2
import psycopg2.extras
import random
import string
import json

from distutils.dir_util import mkpath

import pprint

urls = ('/', 'Index',
		'/receipt/image', 'ReceiptImage',
		'/receipt/(.*)/image', 'ReceiptImage',
		'/collection/(.*)/add/(.*)', 'CollectionAdd',
		'/collection/(.*)', 'Collection',
		'/(.*).json', 'ReportDetails',
		'/(.*)/reimburse', 'ReportReimburse',
		'/(.*)/submit', 'ReportSubmit',
		'/(.*)', 'Report' )

IMG_PATH = 'images/'


def get_db_conn():
	return psycopg2.connect(database='rfser', host='localhost', user='rfser', password='B3zhD9K39:,iq846TjAM%Wz')


def gen_new_id(conn, table):
	random.seed()
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
		raise web.seeother('/' + new_id)


class Report:
	def GET(self, report_id):
		if len(report_id) < 3:
			conn = get_db_conn()
			new_id = gen_new_id(conn, 'report')
			conn.close()
			raise web.seeother('/report/' + new_id)
		return open('index.html').read()

class ReportSubmit:
	def POST(self, report_id):
		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""UPDATE report
		               SET submitted=now()
		               WHERE report_id = %(report_id)s""", {'report_id': report_id})
		conn.commit()
		conn.close()
		return "OK"

class ReportDetails:
	def GET(self, report_id):
		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""SELECT name, employee, COALESCE(TO_CHAR(submitted, 'Mon D, YYYY HH:MMam'), 'No'),
							COALESCE(TO_CHAR(reimbursed, 'Mon D, YYYY HH:MMam'), 'No') 
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

		cur.execute("""SELECT receipt_id, COALESCE(amount,0), COALESCE(description, '')
		               FROM receipt WHERE report_id = %(report_id)s""",
		            {'report_id': report_id})
	
		rows = cur.fetchall();
		jrow = []
		for r in rows:
			jrow.append('{\"receipt_id\": \"%s\",\"amount\": %s, \"description\": \"%s\"}' % (r[0], r[1], r[2]))
		receipts ='[' + ','.join(jrow) + ']'

		conn.close()
		return "{\"reportName\": \"%s\", \"employee\": \"%s\", \"submitted\": \"%s\",\"reimbursed\": \"%s\", \"receipts\": %s}" % (reportName, employee, row[2], row[3], receipts);


	def POST(self, report_id):
		data = web.input()

		try:	
			report = json.loads(data['report'])
		except:
			raise web.badrequest()	
		report['report_id'] = report_id;

		if 'reportName' not in report.keys():
			return web.badrequest()
		if 'employee' not in report.keys():
			return web.badrequest()

		conn = get_db_conn()
		cur = conn.cursor()

		if len(report['reportName']) > 3:
			cur.execute("""UPDATE report
		                   SET name=%(reportName)s, saved=now() 
		                   WHERE report_id = %(report_id)s""", report)

		if len(report['employee']) > 2:
			cur.execute("""UPDATE report
		                   SET employee=%(employee)s, saved=now() 
		                   WHERE report_id = %(report_id)s""", report)
		conn.commit()

		for r in report['receipts']:
			r['report_id'] = report_id

			try: 
				float(r['amount'])
			except ValueError:
				r['amount'] = None
			
			cur.execute("""UPDATE receipt 
		   	            SET amount=%(amount)s, description = %(description)s 
		   	            WHERE receipt_id = %(receipt_id)s AND report_id = %(report_id)s""", r)
		conn.commit()

		conn.close()
		return "OK"

class ReportReimburse:
	def POST(self, report_id):
		conn = get_db_conn()
		cur = conn.cursor()
		cur.execute("""UPDATE report SET reimbursed = now() WHERE reimbursed IS NULL AND report_id=%(report_id)s""", {'report_id': report_id});
		conn.commit()
		conn.close()
		
		return "OK"

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

		print "\n\nGENERATING IMAGE report: %s -> receipt: %s\n\n" % (report_id, receipt_id);

		return '{"receipt_id" : \"%s\"}' % receipt_id

	def GET(self, receipt_id):
		if len(receipt_id) < 4:
			return web.badrequest()
		path = IMG_PATH + receipt_id[0] + '/' + receipt_id[1] + '/'
		fp = open(path + receipt_id + "_original")
		img = fp.read()
		fp.close()
		return img

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


