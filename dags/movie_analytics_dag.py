from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import random
import time

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Function to simulate work with random duration
def process_data(platform, genre, **context):
    print(f"Processing {genre} movies from {platform}")
    # Simulate varying workloads
    time.sleep(random.uniform(1, 5))
    return random.randint(100, 1000)  # Return random number of processed movies

# Function to aggregate results
def aggregate_results(**context):
    task_instances = context['task_instance']
    platforms = ['Netflix', 'Prime', 'Disney', 'HBO']
    genres = ['Action', 'Comedy', 'Drama', 'SciFi', 'Horror']
    
    total = 0
    for platform in platforms:
        for genre in genres:
            task_id = f'process_{platform.lower()}_{genre.lower()}'
            result = task_instances.xcom_pull(task_ids=task_id)
            if result:
                total += result
    
    print(f"Total movies processed: {total}")
    return total

with DAG(
    'movie_analytics_demo',
    default_args=default_args,
    description='A demo DAG processing movie data across platforms and genres',
    schedule_interval='@daily',
    start_date=datetime(2023, 12, 4),  # 7 days ago
    catchup=True,
    tags=['demo'],
    #max_active_runs=3,
    #concurrency=20,
) as dag:

    # Create tasks for each platform and genre combination
    platforms = ['Netflix', 'Prime', 'Disney', 'HBO']
    genres = ['Action', 'Comedy', 'Drama', 'SciFi', 'Horror']
    
    processing_tasks = {}
    
    # Generate processing tasks for each platform-genre combination
    for platform in platforms:
        for genre in genres:
            task_id = f'process_{platform.lower()}_{genre.lower()}'
            processing_tasks[(platform, genre)] = PythonOperator(
                task_id=task_id,
                python_callable=process_data,
                op_kwargs={'platform': platform, 'genre': genre},
            )

    # Create platform-specific aggregation tasks
    platform_aggregations = {}
    for platform in platforms:
        platform_aggregations[platform] = PythonOperator(
            task_id=f'aggregate_{platform.lower()}',
            python_callable=aggregate_results,
        )
        # Set dependencies: all genre tasks for this platform must complete before aggregation
        for genre in genres:
            processing_tasks[(platform, genre)] >> platform_aggregations[platform]

    # Final aggregation task
    final_aggregate = PythonOperator(
        task_id='final_aggregate',
        python_callable=aggregate_results,
    )

    # Set dependencies for final aggregation
    for platform in platforms:
        platform_aggregations[platform] >> final_aggregate
