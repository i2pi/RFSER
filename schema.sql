DROP TABLE report CASCADE;
CREATE TABLE report (
	report_id	TEXT PRIMARY KEY,
	created		TIMESTAMP DEFAULT now(),
	submitted	TIMESTAMP,
	reimbursed	TIMESTAMP,
	name		TEXT,
	employee	TEXT
);

DROP TABLE receipt CASCADE;
CREATE TABLE receipt (
	receipt_id	TEXT PRIMARY KEY,
	report_id	TEXT REFERENCES report(report_id),
	description	TEXT,
	amount		NUMERIC(16,4)
);


DROP TABLE collection CASCADE;
CREATE TABLE collection (
	collection_id	TEXT PRIMARY KEY
);

DROP TABLE collection_report;
CREATE TABLE collection_report (
	collection_id	TEXT REFERENCES collection(collection_id),
	report_id	TEXT REFERENCES report(report_id)	
);
CREATE INDEX collection_report_collection_idx ON collection_report(collection_id);
