# Airflow Test
> Based on: [puckel/docker-airflow](https://github.com/puckel/docker-airflow)

This part is to assess candidates' Python skills, especially in using Airflow and Pandas for data engineering. The candidate is required to submit the whole repo after finish.

## What this repo contains
```
├── README.md
├── dags
│   ├── input
│   │   └── spins_and_freespins.csv
│   ├── output
│   │   └── players_award.csv           (will be created by your DAG)
│   └── spins_and_freespins_process.py  (currently it is empty, and you will work on this script to creata a DAG)
└── docker-compose.yml
```

## Instructions
- Install Docker
- Open this repo as workspace
- Run below to start the containers in the background: (It will build the Docker images the first time you run it)
```bash
docker-compose up -d
```
- Write a script in `dags/spins_and_freespins_process.py` to create a DAG
    - the DAG is to calculate chips award of all players according to `Question 2 – Free Spin Sessions`
    - the calculation result should be exported to  `dags/output/players_award.csv`
    - the columns of `dags/output/players_award.csv` :
        - `Playerid`
        - `ChipsAwarded`
        - `DollarsAwarded`
- Go to `http://localhost:8080/admin/` and trigger the DAG. After DAG run, you should be able to see the exported csv in `dags/output/`
- Submit the whole repo


## Clean up
```bash
docker-compose down --rmi all
```
