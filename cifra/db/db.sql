CREATE TABLE IF NOT EXISTS 'user' (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
  user_title TEXT NOT NULL, 
  user_hash TEXT NOT NULL, 
  user_admin INTEGER DEFAULT 0,
  UNIQUE (user_title, user_hash)  
);

CREATE TABLE  IF NOT EXISTS 'category'(
   category_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   category_title TEXT NOT NULL,
   category_process INTEGER NOT NULL,
   category_active INTEGER DEFAULT 1,
   category_sortby INTEGER DEFAULT 0,
   UNIQUE (category_title, category_process)
);

CREATE TABLE  IF NOT EXISTS 'density'(
   density_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   density_density INTEGER NOT NULL UNIQUE
);

CREATE TABLE  IF NOT EXISTS 'unit'(
   unit_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   unit_title TEXT NOT NULL UNIQUE
);

CREATE TABLE  IF NOT EXISTS 'size'(
   size_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   size_title TEXT,
   size_width INTEGER NOT NULL,
   size_height INTEGER NOT NULL,
   UNIQUE (size_width, size_height)
);

CREATE TABLE  IF NOT EXISTS 'material'(
   material_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   material_title TEXT NOT NULL,
   material_active INTEGER DEFAULT 0,
   material_amount INTEGER DEFAULT 0,
   size_id INTEGER NOT NULL,
   category_id INTEGER NOT NULL,
   unit_id INTEGER NOT NULL,
   density_id INTEGER NOT NULL,
   material_minimum INTEGER DEFAULT 1,
   FOREIGN KEY(category_id) REFERENCES category(category_id),
   FOREIGN KEY(unit_id) REFERENCES unit(unit_id),
   FOREIGN KEY(size_id) REFERENCES size(size_id),
   FOREIGN KEY(density_id) REFERENCES size(density_id),
   UNIQUE (material_title, size_id, category_id, density_id),
   CHECK(material_amount >= 0)
);

CREATE TABLE  IF NOT EXISTS 'log'(
   log_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
   log_title TEXT,
   log_action INTEGER NOT NULL,
   log_amount INTEGER NOT NULL,
   log_time INTEGER NOT NULL,
   log_info TEXT,
   material_id INTEGER NOT NULL,
   user_id INTEGER NOT NULL,
   FOREIGN KEY(material_id) REFERENCES material(material_id),
   FOREIGN KEY(user_id) REFERENCES user(user_id)
);



INSERT INTO user (user_title,user_hash,user_admin)
	VALUES ('admin','21232f297a57a5a743894a0e4a801fc3',1);