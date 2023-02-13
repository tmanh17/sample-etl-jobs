# playstudito

Some notes:

* To simplify I've just used a MySQL configuration in the app/config.json file as the following without passing them via variable environments.
```
"mysql_settings": {
    "host": "localhost",
    "port": 3306,
    "database": "playstudio",
    "user": "root",
    "password": ""
}
```

## Section1
For this section please provide.

a) A copy of the code you created

The code is located in the folder app, the main file is app/main.py

b) A summary of how the code works

In this assessment, I use MySQL as the target database. Thus, We need to prepare MySQL tables by running DDL queries in the files database/playstudio.events.sql and database/playstudio.palyers.sql. In addition, The code is designed to insert data into the table by day. The steps will be as the following.

* Delete data of the input data in the tables
* Read the CSV file batch by batch, and convert data in the file to the Insert SQL queries to insert into the table.

Steps to run the code:

* Run initial data for EventData
```
app git:(main) ✗ ./main.py -s 2022-11-11 -e 2022-11-12
```
* Run initial data for PlayerData
```
app git:(main) ✗ ./main.py -s 2019-12-12 -e 2020-01-13
```
c) Notes on any rework or issues found while running the job

In case the job is failed while running we can simply re-run it because the job performs delete data first and re-insert after that. Thus, duplication or missing data will not happen. I also added two columns datafile_date and processed_time for all tables. where datafile_date is the suffix of the file we used to insert data, and processed_time is the time that data is inserted into the table, in case we have a problem with data and would like to check whether issues are from our data pipeline or they are from the original file we can check it easily. For instance, if we found that some records are missing from the table. we can compare data in the file and the data in the table by filtering datafile_date. Furthermore, we can compare processed_time with the last time the file is updated to make sure the file is not updated after the daily job run.


d) Any feature you would like to have added which you did not have time to include

One of the features I’d like to add is split files into smaller trunks and insert them into the database in parallel so that data will be updated more quicker.

## Section 2:

The content of the repo containing your code and the output file with data

The code is located in airflow-pipeline-test/spins_and_freespins_process.py
Output file is airflow-pipeline-test/output/players_award.csv

## Section 3:

a) A copy of the database used for the analysis, a compressed back-up - A summary of the content of the database

The copy of the database is database/playstudio_backup.sql
the database contain 2 tables for loading data from two type of files EventData and PlayerData.

b) A copy of the SQL code used to calculate the answers

Will be noted for each Question below.

c) Notes on any optimizations applied to the database

To speed up the performance of the query I've created an index on the id column.

* On playstudio.players table

```
CREATE INDEX idx1 ON playstudio.players (id);
```

### Question 1:


```
SELECT 
    install_date
    ,ROUND(total_user_active_D3 / total_installed_users_D0 * 100, 2) retention_D3
    ,total_spent_by_D7/total_installed_users_D0 AS ARPI_D7
FROM (
    SELECT 
        install_date, sum(online_D3) total_user_active_D3, count(1) AS total_installed_users_D0, SUM(IFNULL(spent_by_D7, 0)) AS total_spent_by_D7
    FROM (
        SELECT  
            CAST(T1.install_date AS DATE) install_date
            ,T1.id
            ,CASE 
                WHEN T2.login_date IS NULL THEN 0
                ELSE 1
            END online_D3
            ,(
                SELECT SUM(revenue) FROM playstudio.players Y
                WHERE Y.id = T1.id
                AND CAST(Y.login_date AS DATE) BETWEEN CAST(T1.install_date AS DATE) AND CAST(T1.install_date AS DATE) + 7
            ) AS spent_by_D7
        FROM playstudio.players T1
        LEFT JOIN playstudio.players T2
            ON T1.id = T2.id
            AND CAST(T1.install_date AS DATE) + 3 = CAST(T2.login_date  AS DATE)
    ) X1
    GROUP BY install_date
) X2
ORDER BY install_date;
```

### Question 2:


There are different approaches to solving this problem:

a) the first approach: create a procedure and temporary table for query result data.

```
CREATE PROCEDURE CALC_AWARDS()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_id, v_play_bet BIGINT;
    DECLARE v_play_win DECIMAL(20,5);
    DECLARE v_prev_id BIGINT DEFAULT -1;
    DECLARE v_cum_sum DECIMAL(20,5) DEFAULT 0;
  
    DECLARE cur_events CURSOR FOR 
        SELECT id, play_bet, IFNULL(play_win, 0) AS play_win 
        FROM playstudio.events
        WHERE play_bet IS NOT NULL
        ORDER BY id, event_time;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    DROP TABLE IF EXISTS playstudio.awards;
    CREATE TEMPORARY TABLE playstudio.awards (id BIGINT PRIMARY KEY, play_win DECIMAL(20, 5));

    OPEN cur_events;
  
    events_loop: LOOP
        FETCH cur_events INTO v_id, v_play_bet, v_play_win;
        IF done THEN
        -- handle the last session in case the last event has play_bet = 0
        IF v_prev_id <> -1 THEN
	        INSERT INTO playstudio.awards (id, play_win) VALUES (v_prev_id, v_cum_sum)
	        	ON DUPLICATE KEY UPDATE play_win = GREATEST(play_win, v_cum_sum);
	    END IF;
        LEAVE events_loop;
        END IF;
        IF v_play_bet <> 0 THEN -- session is terminated
        	IF v_prev_id <> -1 THEN
	            INSERT INTO playstudio.awards (id, play_win) VALUES (v_prev_id, v_cum_sum)
	                ON DUPLICATE KEY UPDATE play_win = GREATEST(play_win, v_cum_sum);
	    	END IF;
	            SET v_cum_sum = 0;
            SET v_prev_id = v_id;
            
        ELSEIF v_prev_id <> v_id THEN -- session is terminated and start to calculate for a new player.
        	IF v_prev_id <> -1 THEN
	            INSERT INTO playstudio.awards (id, play_win) VALUES (v_prev_id, v_cum_sum)
	            	ON DUPLICATE KEY UPDATE play_win = GREATEST(play_win, v_cum_sum);
			END IF;
            SET v_cum_sum = v_play_win;
            SET v_prev_id = v_id;
        ELSE
            SET v_cum_sum = v_cum_sum + v_play_win;
        END IF;
    END LOOP;

    CLOSE cur_events;
END;

CALL CALC_AWARDS();


SELECT 
    id AS PlayerId, 
    play_win * 3 AS ChipsAwarded, 
    ROUND(play_win * 3 / 10000000, 2) AS DollarsAwarded 
FROM playstudio.awards;
```

b) the second approach: using a SQL query, however, the performance is not really good although I tried to use indexes on the table in order to make the sub-queries run faster.
```
SELECT 
	id
	,max(total_win)
FROM (
	SELECT 
		T1.id,
		(
		SELECT SUM(play_win) FROM playstudio.events X1
		WHERE id = T1.id
		AND event_time >= T1.event_time AND event_time < (
				SELECT min(event_time) FROM playstudio.events X2 
				WHERE id = X1.id
				AND event_time > T1.event_time AND play_bet > 0
			)
		) AS total_win
	FROM playstudio.events T1
	WHERE 1 = 1
	AND play_bet = 0 and play_win <> 0
	--AND id IN( 28, 308, 1356)
) Y
GROUP BY id;
```

### Question 3 – AB Test
To select which group should be rolled out. We should understand the purpose of this test. after that, By checking metrics related to groups we can figure out which group more satisfies our expectations. It's supposed to be a lot of other metrics that should be taken into consideration. For the purpose of this test, we have only 4 metrics to consider including Spins, MeanWager, PreferredGame, and Spend. I suppose that the most important metric here is spending.

It seems that group B is the current approach as I can all metrics are quite balanced. But group A has an unbalanced metrics bias to the DragonGame game. I suppose that we are running a test that encourages players to play more DragonGame. However, it makes the spending of other metrics reduced and the total of spend is reduced significantly. It means that we should roll out group B.

=> More detailed information about the analysis is in the Jupyter notebook file abtest_analysis.ipynb

### Question 4 – Projects (Bonus)

we are aiming to design our system toward a microservice architecture that brings a lot of benefits by applying DevOps best practices for driving higher software delivery performance and establishing a healthy organization (refer https://services.google.com/fh/files/misc/dora_research_program.pdf https://cloud.google.com/architecture/devops). In addition, I worked in a scrum team. I understand how it works and the roles of different positions in the team. How they contribute to the velocity of the team and the values they bring to the team and for the company
 
 
In addition, I worked with Airflow for quite a while. Which is sufficient to design DAG suitably in the Citigo company that I mentioned in the resume. The second one is in Coccoc, we try to understand whether Airflow is suitable for visualizing our data pipeline?. Eventually, After reading some articles combine with my experience of mine and my teammates' about airflow. We ended up deciding not to use it because of its drawbacks. The main drawbacks is that Airflow is monolithic. As mentioned earlier, Monolithic is the opposite of our Microservice architecture which is not really good for our architecture and our way of managing tasks.


Steps to run file, please ignote password in the log file. For simplify reproducing process. I've just setup an Mysql account using root user without password in the app/config.json file
# simple_etl_jobs
