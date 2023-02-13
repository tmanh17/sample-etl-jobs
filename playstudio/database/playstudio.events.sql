--DDL for creating the table
--DROP TABLE playstudio.events;
CREATE TABLE playstudio.events (
    datafile_date TEXT,
    processed_time DATETIME DEFAULT now(),
    id BIGINT,
    event_time DATETIME,
    play_bet BIGINT,
    play_win DECIMAL(20,5),
    altid_supid TEXT,
    altid_socid TEXT,
    device_id TEXT,
    device_id_type_os TEXT,
    device_id_type_model TEXT,
    device_platform TEXT
);

-- Section 2
-- Using procedure

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

-- Using SQL query

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
	-- AND id IN( 28, 308, 1356)
) Y
GROUP BY id;
