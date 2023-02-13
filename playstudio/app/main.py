#!/usr/bin/env python3

import click
import json
from loguru import logger
from datetime import date, timedelta, datetime
from mysql_helper import create_db_conn, delete_date, insert_date
from converter import event_converter, player_converter
import os

db_conn = create_db_conn()

def load_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
        return data

def run(start_date, end_date, database, table):
    config = load_config()
    database_table = database + "." + table
    table_config = config['schemas'][database_table]
    path = table_config['path']

    logger.info(f"{path}: {start_date} - {end_date} ({database_table})")
    batch_size = table_config['batch_size'] if 'batch_size' in table_config.keys() else config['default']['batch_size']
    dir_list = os.listdir(path)
    print("Files and directories in '", path, "' :", dir_list)

    data_converter = {
        'playstudio.events': event_converter,
        'playstudio.players': player_converter
    }[database_table]

    while start_date <= end_date:
        run_date = start_date.strftime("%Y%m%d")
        run_file = "{}_{}.{}".format(table_config['file_prefix'], run_date, table_config['file_extension'])
        columns = table_config['columns']
        if run_file not in dir_list:
            logger.warning("Does not found {}", path + "/" + run_file)
        else:
            logger.info("Deleting data of {} for table {}", run_date, database_table, path, run_file)
            delete_date(db_conn, database, table, run_date)
            logger.info("Inserting data for the table {} using {}/{}", database_table, path, run_file)
            lines = open("{}/{}".format(path, run_file), "r", encoding='utf-8-sig')
            cnt = 0
            rows = []
            for line in lines:
                cnt += 1
                rows.append(data_converter(line, run_date))
                if len(rows) >= batch_size:
                    insert_date(db_conn, database, table, columns, rows )
                    rows.clear()
                    logger.info("Running for table {} using {}/{} inserted {}",database_table, path, run_file, cnt)
            if len(rows) > 0:
                insert_date(db_conn, database, table, columns, rows )
                rows.clear()
                logger.info("Running for table {} using {}/{} inserted {}",database_table, path, run_file, cnt)

        start_date = start_date + timedelta(days=1)

@click.command()
@click.option('-s', '--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), default=str(date.today() - timedelta(days=1)), help='Start date.')
@click.option('-e', '--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), default=str(date.today() - timedelta(days=1)), help='End date.')
@click.argument('table', default="")
@logger.catch
def main(table, start_date, end_date):
    config = load_config()
    for db_table in config['schemas'].keys():
        db_name, table_name = db_table.split(".")
        if table == "" or table == db_table:
            run(start_date, end_date, db_name, table_name)

if __name__ == '__main__':
    main()


