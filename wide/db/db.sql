CREATE TABLE  IF NOT EXISTS 'category'(
   category_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   category_title TEXT NOT NULL UNIQUE,
   category_active INTEGER DEFAULT 1,
   category_sortby INTEGER DEFAULT 0
);

CREATE TABLE  IF NOT EXISTS 'size'(
   size_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   size_title TEXT NOT NULL,
   size_p1 INTEGER DEFAULT 0,
   size_p2 INTEGER DEFAULT 0,
   category_id INTEGER,
   FOREIGN KEY(category_id) REFERENCES category(category_id),
   UNIQUE (size_title, category_id)
);

CREATE TABLE  IF NOT EXISTS 'unit'(
   unit_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   unit_title TEXT NOT NULL UNIQUE
);

CREATE TABLE  IF NOT EXISTS 'material'(
   material_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   symbol_id INTEGER NOT NULL,
   material_title TEXT NOT NULL,
   size_id INTEGER NOT NULL,
   material_amount INTEGER DEFAULT 0,
   material_minimal	INTEGER DEFAULT 0,
   category_id INTEGER NOT NULL,
   unit_id INTEGER NOT NULL,
   material_active INTEGER DEFAULT 1,
   material_capacity INTEGER DEFAULT 1,
   material_info TEXT,
   FOREIGN KEY(category_id) REFERENCES category(category_id),
   FOREIGN KEY(unit_id) REFERENCES unit(unit_id),
   FOREIGN KEY(size_id) REFERENCES size(size_id),
   FOREIGN KEY(symbol_id) REFERENCES symbol(symbol_id),
   UNIQUE (material_title, size_id),
   CHECK(material_amount >= 0 and material_minimal >= 0)
);

CREATE TABLE  IF NOT EXISTS 'symbol'(
   symbol_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   symbol_title TEXT NOT NULL UNIQUE,
   category_id INTEGER,
   FOREIGN KEY(category_id) REFERENCES category(category_id)
);

CREATE TABLE IF NOT EXISTS 'user' (
  'user_id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
  'user_title' TEXT NOT NULL UNIQUE, 
  'user_hash' TEXT NOT NULL UNIQUE, 
  'user_admin' INTEGER DEFAULT 0 
);

CREATE TABLE  IF NOT EXISTS 'log'(
   log_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   log_info TEXT,
   log_action INTEGER NOT NULL,
   log_amount INTEGER NOT NULL,
   log_time INTEGER NOT NULL,
   material_id INTEGER NOT NULL,
   user_id INTEGER NOT NULL,
   log_stock INTEGER NOT NULL,
   FOREIGN KEY(material_id) REFERENCES material(material_id),
   FOREIGN KEY(user_id) REFERENCES user(user_id)
);

CREATE TABLE  IF NOT EXISTS 'sorder'(
   sorder_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   sorder_title TEXT,
   sorder_timeopen DATETIME NOT NULL,
   sorder_timeclose DATETIME DEFAULT (datetime('2000-01-01 00:00:00.00000')),
   sorder_comment TEXT,
   sorder_status INTEGER DEFAULT 0,
   user_id INTEGER NOT NULL,
   FOREIGN KEY(user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS request (
	request_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	material_id INTEGER NOT NULL,
	sorder_id INTEGER DEFAULT 0,
	request_comment TEXT,
	request_amount INTEGER NOT NULL,
	request_result DEFAULT 0,
	request_timeopen DATETIME NOT NULL,
	request_timeclose DATETIME,
	user_id INTEGER NOT NULL,
	FOREIGN KEY (material_id)  REFERENCES material(material_id),
	FOREIGN KEY (sorder_id)  REFERENCES sorder(sorder_id),
	FOREIGN KEY(user_id) REFERENCES user(user_id),
	UNIQUE (material_id, sorder_id)
);	

CREATE TABLE IF NOT EXISTS contractor (
   contractor_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   contractor_title TEXT NOT NULL,
   contractor_info TEXT,
   UNIQUE (contractor_title)
);
	
CREATE TABLE IF NOT EXISTS reserve (
   reserve_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   reserve_amount INTEGER DEFAULT 0,
   material_id INTEGER NOT NULL,
   contractor_id INTEGER NOT NULL,
   FOREIGN KEY(material_id) REFERENCES material(material_id),
   FOREIGN KEY(contractor_id) REFERENCES contractor(contractor_id),
   UNIQUE (material_id, contractor_id),
   CHECK(reserve_amount >= 0)
);	