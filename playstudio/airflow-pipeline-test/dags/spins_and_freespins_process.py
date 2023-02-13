from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
import pandas as pd

default_args = {
		'owner': 'manhdt',
		'start_date': datetime(2022, 1, 1),
		# 'retries': 3,
		# 'retry_delay': timedelta(minutes=5)
}

def calc_awards():
    df = pd.read_csv('dags/input/spins_and_freespins.csv', names=["id", "event_time", "play_bet", "play_win"])

    df = df.sort_values(by=['id', 'event_time'])
    player_ids = df['id'].unique()
    df['value'] = (df[['id', 'play_bet']] != df[['id', 'play_bet']].shift()).any(axis=1)
    df['value'] = df['value'].cumsum()
    df = df[df['play_bet']==0]
    df = df.groupby(['id','value'])['play_win'].sum().reset_index()
    df = df.groupby('id')['play_win'].max().reset_index()
    df['PlayerId'] = df['id']
    df['ChipsAwarded'] = df['play_win'] * 3
    df['DollarsAwarded'] = df['ChipsAwarded'] / 10000000 
    df = df[["PlayerId","ChipsAwarded","DollarsAwarded"]]

    remaining_list  = [[id,0,0] for id in player_ids if id not in list(df['PlayerId'])]
    remaining_df = pd.DataFrame(remaining_list, columns =['PlayerId', 'ChipsAwarded','DollarsAwarded'])
    res = df.append(remaining_df, ignore_index=True)
    res = res.sort_values(by='PlayerId')
    res.to_csv('dags/output/players_award.csv', index=False)

calc_awards_dag = DAG('calc_awards_dag', 
    default_args=default_args,
    description='calc awards',
    schedule_interval='0 12 * * *',
    catchup=False,
)


calc_awards_job = PythonOperator(task_id='calc_awards', python_callable=calc_awards, dag=calc_awards_dag)
calc_awards_job