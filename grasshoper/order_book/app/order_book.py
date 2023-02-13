import threading
import time
import csv
import click
from queue import PriorityQueue
from loguru import logger
from datetime import datetime, timezone

PRIORITY_QUEUE_ORDER = {"BUY": -1, "SELL": 1}
accumulative_orders = {"BUY": PriorityQueue(), "SELL": PriorityQueue()}
future_queue = PriorityQueue()
orderid_2_values = {"BUY" :{}, "SELL": {}}
price_2_qty = {"BUY" :{}, "SELL": {}}

def to_int(value):
    return int(value) if value else 0

def to_float(value):
    return float(value) if value else 0.0

def transform(o):
    ans = {}
    ans['op'] = 'ADD' if o['add_order_id'] else 'UPDATE' if o['update_order_id'] else 'DELETE' if o['delete_order_id'] else 'TRADE'
    ans['order_id'] = o['add_order_id'] + o['update_order_id'] + o['delete_order_id'] + o['trade_order_id']
    ans['side'] = o['add_side'] + o['update_side'] + o['delete_side'] + o['trade_side']
    ans['time'] = datetime.strptime(o['time'], '%Y-%m-%d %H:%M:%S.%f %Z').replace(tzinfo=timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
    ans['seq_num'] = int(o['seq_num'])
    ans['price'] = to_float(o['add_price']) + to_float(o['update_price']) + to_float(o['trade_price'])
    ans['qty'] = to_int(o['add_qty']) + to_int(o['update_qty']) + to_int(o['trade_qty'])

    return ans

def handle_add_or_update(o):
    op, order_id, side, price, qty, time, seq = o['op'], o['order_id'], o['side'], o['price'], o['qty'], o['time'], o['seq_num']
    prev_price, prev_qty = orderid_2_values[side].get(order_id, (0, 0)) # keep the previous price, qty of orderid. (0, 0) in case of a new order
    orderid_2_values[side][order_id] = (price, qty) # update price and qty for orderId
    price_2_qty[side][prev_price] = price_2_qty[side].get(prev_price, 0) - prev_qty # decrease qty of previous price. prev_qty = 0 in case of a new order
    price_2_qty[side][price] = price_2_qty[side].get(price, 0) + qty # add more qty to the new price
    accumulative_orders[side].put((price * PRIORITY_QUEUE_ORDER[side], price, price_2_qty[side][price], time, seq)) # add to the bbo queue

def handle_delete(o):
    op, order_id, side, price, qty, time, seq = o['op'], o['order_id'], o['side'], o['price'], o['qty'], o['time'], o['seq_num']
    price, qty = orderid_2_values[side][order_id] # get price, qty of orderid
    orderid_2_values[side].pop(order_id, None) # remove order_id from dictionary
    price_2_qty[side][price] -= qty # decrease qty of price
    accumulative_orders[side].put((price * PRIORITY_QUEUE_ORDER[side], price, price_2_qty[side][price], time, seq))
    
def handle_trade(o):
    op, order_id, side, price, qty, time, seq = o['op'], o['order_id'], o['side'], o['price'], o['qty'], o['time'], o['seq_num']
    _, prev_qty = orderid_2_values[side][order_id]
    price_2_qty[side][price] -= qty
    orderid_2_values[side][order_id] = (price, prev_qty - qty)
    accumulative_orders[side].put((price * PRIORITY_QUEUE_ORDER[side], price, price_2_qty[side][price], time, seq))

def event_producer_thread(future_queue, input_file_path):
    with open(input_file_path, 'r') as f:
        reader = csv.reader(f)
        next(f) #skip header
        for row in reader:
            o = transform({
                'seq_num': row[0],
                'add_order_id': row[1],
                'add_side': row[2],
                'add_price': row[3],
                'add_qty': row[4],
                'update_order_id': row[5],
                'update_side': row[6],
                'update_price': row[7],
                'update_qty': row[8],
                'delete_order_id': row[9],
                'delete_side': row[10],
                'trade_order_id': row[11],
                'trade_side': row[12],
                'trade_price': row[13],
                'trade_qty': row[14],
                'time': row[15]})

            future_queue.put((o['seq_num'], o))

def event_consumer_thread(future_queue, output_file, batch_size, max_flush_interval):
    global accumulative_orders, PRIORITY_QUEUE_ORDER, orderid_2_values, price_2_qty
    file_header = ["time","bid_price","ask_price","bid_size","ask_size","seq_num"]
    f = open(output_file, "w")
    f.write(','.join(file_header) + "\n")
    f.close()

    next_seq, ask_bid = -1, ()
    while True:
        # handle events by batch util reach batch_size or max flush interval is reached
        if future_queue.qsize() < batch_size:
            time.sleep(max_flush_interval)
        
        next_seq = future_queue.queue[0][1]['seq_num'] if not future_queue.empty() and next_seq == -1 else next_seq
        processed_cnt = 0
        
        while not future_queue.empty() and processed_cnt < batch_size:
            f = open(output_file, "a")
            if future_queue.queue[0][1]['seq_num'] != next_seq:
                break

            o = future_queue.queue[0][1]
            future_queue.get()
            next_seq, processed_cnt = next_seq + 1, processed_cnt + 1
            
            if o['op'] == 'ADD' or o['op'] == 'UPDATE':
                handle_add_or_update(o)
            elif o['op'] == 'DELETE':
                handle_delete(o)
            else:
                handle_trade(o)
            
            # Remove outdated bbo records in the priority queue that qty of price is changed due to update or delete or trade
            for s in ['BUY','SELL']:
                while not accumulative_orders[s].empty():
                    price, qty = accumulative_orders[s].queue[0][1], accumulative_orders[s].queue[0][2]
                    actual_qty = price_2_qty[s][price]
                    if qty != 0 and actual_qty == qty:
                        break
                    accumulative_orders[s].get()
            
            # Get top element of each queue (buy & sell orders)
            if not accumulative_orders['BUY'].empty() and not accumulative_orders['SELL'].empty():
                ask, ask_size = accumulative_orders['BUY'].queue[0][1], accumulative_orders['BUY'].queue[0][2]
                bid, bid_size = accumulative_orders['SELL'].queue[0][1], accumulative_orders['SELL'].queue[0][2]

                new_ask_bid = (ask, bid, ask_size, bid_size)
                if ask_bid != new_ask_bid:
                    f.write("{},{},{},{},{},{}\n".format(o['time'], ask, bid, int(ask_size), int(bid_size), o['seq_num']))
                    ask_bid = new_ask_bid
        
        if processed_cnt == 0:
            logger.info("Handled all events, the output file is {}. No new events in the last {} seconds.".format(output_file, max_flush_interval))
            
        f.close()


def run(input_file, output_file, batch_size, max_flush_interval):
    producer_thread = threading.Thread(target=event_producer_thread, args=(future_queue, input_file), daemon=True).start()
    consumer_thread = threading.Thread(target=event_consumer_thread, args=(future_queue, output_file, batch_size, max_flush_interval), daemon=True).start()

