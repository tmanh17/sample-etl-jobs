# Script to run the program. 

Please DM me via skype `live:tmanh17` if you still find it difficult to run the program

At the very first step, go to the project directory `order_book`
```
manhdt@manhdts-MacBook-Pro order_book % ls
Dockerfile                      __pycache__                     expected_l1_data_v3.1.csv       readme.md
Makefile                        app                             l3_data_v3.1.csv                requirements.txt
```
The code provides 2 options to run the program will be explained as the following

## 1. Setup python environment and run the python script
[Install python](https://phoenixnap.com/kb/how-to-install-python-3-ubuntu)
### 1.1. Install needed packages
```
pip3 install -U pip && pip3 install -r requirements.txt
```
### 1.2. Run the python script:
```
python3 app/main.py
```
### 1.3. Check logs and check if the output file is as expected:
As it's a streaming processing, we need to use `Ctrl + C` to abort if the output file is generated fully
```
manhdt@manhdts-MacBook-Pro order_book % python3 app/main.py
2022-12-05 00:55:21.891 | INFO     | __main__:main:15 - Running Input_file: l3_data_v3.1.csv, output_file: l1_data.csv, batch_size: 1000, flush_time: 2 seconds.
2022-12-05 00:55:28.753 | INFO     | order_book:event_consumer_thread:130 - Handled all events, the output file is l1_data.csv. No new events in the last 2 seconds.
^C
Aborted!

manhdt@manhdts-MacBook-Pro order_book % ls
Dockerfile                      app                             l3_data_v3.1.csv
Makefile                        expected_l1_data_v3.1.csv       readme.md
__pycache__                     l1_data.csv                     requirements.txt
```
Compare 2 files, they have the same checksum value `03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f`. Thus, the output file is as expected
 
```
manhdt@manhdts-MacBook-Pro order_book % shasum -a 256 l1_data.csv expected_l1_data_v3.1.csv  
03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f  l1_data.csv
03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f  expected_l1_data_v3.1.csv
```

### 4. (optional) Run the program with optional params
```
python3 app/main.py -o new_file.csv -b 5000 -t 3 
```
The meaning of parameters is as the following
```
manhdt@manhdts-MacBook-Pro order_book % python3 app/main.py --help
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

## 2. Setup docker environment and run the docker image
[Setup Docker for Ubuntu & Debian](https://docs.docker.com/engine/install/ubuntu/)

### 2.1. Build docker images 
(the meaning of `make docker` is in the `Makefile file`)

Command to build the docker file

```
TAG=v2022.12.05 make docker
```
Build logs
```
manhdt@manhdts-MacBook-Pro order_book % TAG=v2022.12.05 make docker
docker build -t order_book:v2022.12.05 .
[+] Building 2.3s (12/12) FINISHED                                                                                                            
 => [internal] load build definition from Dockerfile                                                                                     0.0s
 => => transferring dockerfile: 37B                                                                                                      0.0s
 => [internal] load .dockerignore                                                                                                        0.0s
 => => transferring context: 2B                                                                                                          0.0s
 => [internal] load metadata for docker.io/library/python:3.7-alpine3.9                                                                  1.9s
 => [1/7] FROM docker.io/library/python:3.7-alpine3.9@sha256:d3953acf09227baf26919dbb4dc3637e8015ce46debbed4cf5444702728cfc16            0.0s
 => [internal] load build context                                                                                                        0.0s
 => => transferring context: 1.23kB                                                                                                      0.0s
 => CACHED [2/7] RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime && echo "Asia/Ho_Chi_Minh" >  /etc/timezo  0.0s
 => CACHED [3/7] COPY requirements.txt /                                                                                                 0.0s
 => CACHED [4/7] RUN pip3 install -U pip     && pip3 install -r /requirements.txt                                                        0.0s
 => [5/7] COPY app /app                                                                                                                  0.1s
 => [6/7] RUN chmod +x /app/main.py                                                                                                      0.2s
 => [7/7] WORKDIR /app                                                                                                                   0.0s
 => exporting to image                                                                                                                   0.0s
 => => exporting layers                                                                                                                  0.0s
 => => writing image sha256:5e5ec4522c591cf153e2723bfad77843944b2f2112acf14033cdc2a206f45f32                                             0.0s
 => => naming to docker.io/library/order_book:v2022.12.05                                                                                0.0s

Use 'docker scan' to run Snyk tests against images to find vulnerabilities and learn how to fix them
docker tag order_book:v2022.12.05 order_book:latest
```
### 2.2. Run the program
we need to mount the directory that contains the input file to `/mnt` inside a docker container and the output file should be placed in `/mnt` directory as well. In addition, As it's a streaming processing, we need to use `Ctrl + C` to abort if the output file is generated fully

Run command:

```
docker run --mount src="$(pwd)",target=/mnt,type=bind order_book:latest /app/main.py -i /mnt/l3_data_v3.1.csv -o /mnt/l1_data_docker.csv
```
Logs:
```
manhdt@manhdts-MacBook-Pro order_book % docker run --mount src="$(pwd)",target=/mnt,type=bind order_book:latest /app/main.py -i /mnt/l3_data_v3.1.csv -o /mnt/l1_data_docker.csv
2022-12-05 01:02:32.445 | INFO     | __main__:main:15 - Running Input_file: /mnt/l3_data_v3.1.csv, output_file: /mnt/l1_data_docker.csv, batch_size: 5000, flush_time: 2 seconds.
2022-12-05 01:03:30.156 | INFO     | order_book:event_consumer_thread:130 - Handled all events, the output file is /mnt/l1_data_docker.csv. No new events in the last 2 seconds.
^C
Aborted!
```
### 2.3. Check the correctness of the output file
```
manhdt@manhdts-MacBook-Pro order_book % shasum -a 256 l1_data_docker.csv expected_l1_data_v3.1.csv 
03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f  l1_data_docker.csv
03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f  expected_l1_data_v3.1.csv
```
Compare 2 files, they have the same checksum value `03c94511a2622e00291341d88f40a964e0b0780765ba01377008132ac768774f`. Thus, the output file is as expected.
# Solution:

Assume that the data set contains full data without missing events which means that it always be present an event with `seq = N + 1` for all `seq_num = N` in the data set where `min(seq_num) <= N < max(seq_num)`. On top of that, duplicates are not present in the file meaning that we don't have 2 events with the same seq_num and in terms of operation, there is no interruption during processing data (for instance, out of memory on the physical server) that requires re-run the job from the middle of processing.
 

## Implementation:

To solve this task, I treated buy orders and sell orders separately, by keeping all active buy orders in descending order of price values and all active sell orders sorted by price in ascending order. we can get the first element in each order (buy and sell orders) and then check if ask, bid, ask_size, or bid_size is updated. If one of them is updated, BBO should be updated respectively.
 
For each Level 3 event, I will update buy and sell orders respectively and re-calculate BBO.


### Some problems should be solved:

**A streaming implementation**: 

In case the data set is really huge. we will not able to load all level 3 data into memory to process and generate Level 1 Data. A streaming implementation should be taken into consideration. In this implementation, I've gone through the input file line by line and cumulated events to small batches the handle them batch by batch.

**How to deal with data which arrives out of order?**

There are some records in the file that are not placed in the correct order of seq_num. for instance, events `1627942268920653180, 1627942268920653182, and 1627942268920653181`. To guarantee events are processed in the right order. I keep tracking a `seq_num` global variable which presents the latest event we processed and the next event has to be seq_num+1, otherwise, we need to wait for the event `seq_num+1` to be put into a future queue to process. In this example, after process `1627942268920653180`, `1627942268920653182` will not be processed right after that because we need to process`1627942268920653181` first. However, if 1627942268920653180 is appear at the beginning of the file and 1627942268920653181 appears at the end of the file, the size of the future queue will keep going and it becomes a loading the full dataset into the memory. when this case exists in real and the memory is not sufficient to store all data. we might need to consider sorting the file by seq_num first using [external sorting](https://www.geeksforgeeks.org/external-sorting/) before starting to process the file line by line. Fortunately, the provided sample dataset does not have that case.
 

**How might it be possible for a unified batch and streaming implementation to work?**

Using a priority queue for the future queue so that the smallest seq_num event will draw out. In addition, maintaining a next_seq number will help to ensure the program always handle an event with `seq_num=N+1` after the event that has `seq_num=N`.
 

### Corner cases to consider:

* The first event appears in the middle of the file. with the streaming implementation. If we don't know the starting of num_seq, the out data will not be correct.

* When the program is interrupted during the data processing. We might need to handle this so that the program can be re-run from the scratch. It requires keeping the last successful event, this can be done easily by an external message queue system like Kafka. On top of that, it requires to keeps states of variables like buy/sells order, and accumulated dictionary, this can be done by storing values in external databases. Especially, in-memory databases like Ignite or Redis.
