import pytz
from datetime import datetime
from MySQLdb import _mysql
from MySQLdb.connections import Connection
import json
def load_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
        return data

def create_db_conn():
    try:
        db_config = load_config()["env_overrides"]["mysql_settings"]
        print(db_config)
        db_conn = Connection(host=db_config['host'], port=db_config['port'], user=db_config['user'],
                                 passwd=db_config['password'], db=db_config['database'], use_unicode=True, charset='utf8mb4')
        return db_conn
    except Exception as e:
        print("Could not create database connection: %s" % str(e))
        raise


def remove_data_by_date(database, table, datafile_date):
    sql = "DELETE FROM {}.{} WHERE datafile_date = '{}'".format(database, table, datafile_date)
    return sql

def generate_insert_query(db_conn, database, table, columns, rows):
    if not all([isinstance(columns, list), isinstance(rows, list)]):
        raise ValueError("Invalid data")

    _columns = ','.join(columns)

    _rs = []
    
    for r in rows:
        _r = '('
        _r += ','.join([sql_value(db_conn, v) for v in r])
        _r += ')'
        _rs.append(_r)
    _rows = ','.join(_rs)

    sql = "INSERT INTO {}.{} ({}) VALUES {}".format(database, table, _columns, _rows)
    
    return sql


def sql_value(db_conn, v):
    if v is None:
        return 'NULL'
    if isinstance(v, bool):
        return f"'{str(int(v))}'"
    # str, object
    return db_conn.literal(str(v)).decode()

def delete_date(db_conn, database, table, datafile_date):
    remove_query = remove_data_by_date(database, table, datafile_date)
    db_conn.query(remove_query)
    db_conn.commit()

def insert_date(db_conn, database, table, columns, rows):
    insert_query = generate_insert_query(db_conn, database, table, columns, rows)
    db_conn.query(insert_query)
    db_conn.commit()