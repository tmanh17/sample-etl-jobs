--DDL for creating the table
--DROP TABLE playstudio.players;
CREATE TABLE playstudio.players (
    datafile_date TEXT,
    processed_time DATETIME DEFAULT now(),
    id BIGINT,
    login_date DATETIME,
    install_date DATETIME,
    revenue DECIMAL(20, 6)
);

CREATE INDEX idx1 ON playstudio.players (id);

--Section 1
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
