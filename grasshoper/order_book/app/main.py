#!/usr/bin/env python3

import time
import click
import order_book
from loguru import logger

@click.command()
@click.option('-i', '--input-file', type=click.STRING, default="l3_data_v3.1.csv", help='L3 data file path.')
@click.option('-o', '--output-file', type=click.STRING, default="l1_data.csv", help='L1 data file path.')
@click.option('-b', '--batch-size', type=click.INT, default=5000, help='Batch size to handle events')
@click.option('-t', '--max-flush-interval', type=click.INT, default=2, help='max flush time in case the batch size can not be reached (in seconds)')
@logger.catch
def main(input_file, output_file, batch_size, max_flush_interval):
    logger.info("Running Input_file: {}, output_file: {}, batch_size: {}, flush_time: {} seconds.".format(input_file, output_file, batch_size, max_flush_interval))
    order_book.run(input_file, output_file, batch_size, max_flush_interval)
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
