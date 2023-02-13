Script to run the program. There are 2 options as the following

Step Go to the project directory
```
manhdt@manhdts-MacBook-Pro order_book % ls
Dockerfile                      __pycache__                     expected_l1_data_v3.1.csv       readme.md
Makefile                        app                             l3_data_v3.1.csv                requirements.txt
```
Install needed packages
```
pip3 install -U pip && pip3 install -r requirements.txt
```
Run manually:
```
python3 app/main.py
```
Logs:
```
manhdt@manhdts-MacBook-Pro order_book % python3 app/main.py
2022-12-04 22:07:32.639 | INFO     | __main__:main:14 - Running Input_file: l3_data_v3.1.csv, output_file: l1_data.csv, batch_size: 1000, flush_time: 10 seconds.
2022-12-04 22:08:03.555 | INFO     | order_book:event_consumer_thread:130 - Handled all events, output file is l1_data.csv. No new events in the last 10 seconds.

manhdt@manhdts-MacBook-Pro Grasshoper % ls
Dockerfile              __pycache__             l1_data.csv             requirements.txt
Makefile                app                     readme.md

-- compare 2 files
manhdt@manhdts-MacBook-Pro Grasshoper % shasum -a 256 l1_data.csv app/expected_l1_data_v3.1.csv 
03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f  l1_data.csv
03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f  app/expected_l1_data_v3.1.csv
```
Run with optional params
```
python3 app/main.py -o new_file.csv -b 5000 -t 3 
```
Where
```
manhdt@manhdts-MacBook-Pro Grasshoper % python3 app/main.py --help
Usage: main.py [OPTIONS]

Options:
  -i, --input-file TEXT           L3 data file path.
  -o, --output-file TEXT          L1 data file path.
  -b, --batch-size INTEGER        Batch size to handle events
  -t, --max-flush-interval INTEGER
                                  max flush time in case the batch size can
                                  not be reached (in seconds)
  --help                          Show this message and exit.
```
Logs:
```
manhdt@manhdts-MacBook-Pro Grasshoper % python3 app/main.py -o new_file.csv -b 5000 -t 3 
2022-12-04 19:17:15.762 | INFO     | __main__:main:14 - Running Input_file: app/l3_data_v3.1.csv, output_file: new_file.csv, batch_size: 5000, flush_time: 3 seconds.
2022-12-04 19:17:25.652 | INFO     | order_book:event_consumer_thread:130 - Handled all events, output file is new_file.csv. No new events in the last 3 seconds.
```


Run using docker:

step 1: build docker
```
TAG=v2022.12.04 make docker
```
step 2: run program
```
sudo docker run -it grasshoper:latest /app/main.py
```

Precondition:

Assume that the data set contains full data without missing events which means that it always be present a event with seq = N + 1 for all seq_num = N in the data set where min(seq_num) <= N < max(seq_num). On top of that, duplicates are not present in the file meaning that we don't have 2 events with the same seq_num and in terms of operation, there are no interuption during processing data (i.e out of memory on the physical server) that requires re-run the job from the middle of processing.

Solution: 

To solve this task, I treated buy orders and sell orders separately, by keeping all active buy orders in descending order of price values and all active sell orders are sorted by price in ascending order. we can get the first elements in each orders (buy and sell orders) then check if ask, bid, ask_size or bid_size is updated. If one of them is updated, I will update OBB respectively.

For each Level 3 events, I will update buy and sell orders respectively and re-caculate OBB.

Some problems should be solved:
* A streaming implementation: In case the data set is really huge. we will not able to load all level 3 data into memory and process to generate level 1 data. Thus, we have to come up with a streaming implementation by going though the file and process events line by line.
* How to deal with data which arrives out of order? There are some records in the file are not placed in the correct order of seq_num. for instance, 1627942268920653180, 1627942268920653182, 1627942268920653181 and 1627942268920653183. To ensure we handle events in the right order. I keep track a seq_num global variable which show us the latest event we processed and the next event have to be seq_num+1, otherwise, events will be put into a future queue for process later. In this example, after process 1627942268920653180, 1627942268920653182 will be put into the future queue. However, if 1627942268920653180 is present at the beginning of the file and 1627942268920653181 appears at the end of the file, the size of future queue will keep going and it becomes loading full dataset into the memory. when this case exists in real and the memory is not able to store all data. we might need to consider sort the file by seq_num first using [external sorting](https://www.geeksforgeeks.org/external-sorting/) before starting to process file line by line. Fortunately, the provided sample dataset does not have that case.
* How might it be possible for a unified batch and streaming implementation to work?
As mentioned earlier, if the seq+1 event is located quite far from seq. it's not really affective to always check if seq+1 appeared in the future queue every time we handle an new event. instead we can load data into the future queue batch by batch, sort events inside the queue by seq_num. and handle events batch by batch.

Corner cases to consider:

* The first event appear at the end of the file. By applying the streaming we can't handle this case because we don't know the starting point of events.

Kafka, inmemory database for handle data from middle of the processing
