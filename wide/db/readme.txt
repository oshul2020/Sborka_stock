open the cmd
SET PGCLIENTENCODING=utf-8
chcp 65001

pg_ctl -D "C:\Program Files\PostgreSQL\11\data" restart
psql -f D:\Temp\Sborka\Sborka\stock\db\db_setup.sql -U sborka -d stock

psql -f file_with_sql.sql
psql -h localhost -U postgres

chcp 1251 - ����� ��������� �������
chcp 65001 - utf8

\i d:/temp/sql/p1.sql; - ������ �������
\l - ������ ���
\d - ������ ������
\d table_name - ������ �������
\du - ������ �������������
\d� - ������ ����
\df - ������ ���������
\z - ����� �������
