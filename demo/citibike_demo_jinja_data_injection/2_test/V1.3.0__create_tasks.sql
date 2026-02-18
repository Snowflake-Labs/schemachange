{% from 'modules/task_operations.j2' import create_task %}

-- Load configuration from YAML file using LocalDataInjection
{% set stage_config = from_yaml('2_test/stages.yaml') %}
{% set trips_definitions = from_csv('2_test/trips.csv', as_dict=true) %}
{% set weather_definitions = from_csv('2_test/weather.csv', as_dict=true) %}

-- Set the database and schema context
USE SCHEMA {{database_name}}.{{schema_name}};

-- Create tasks for processing data from landing to final tables
{% for task in stage_config.tasks %}
    {% if task.name == 'PROCESS_TRIPS_DATA' %}
        {{ create_task(task, trips_definitions) }}
    {% elif task.name == 'PROCESS_WEATHER_DATA' %}
        {{ create_task(task, weather_definitions) }}
    {% endif %}
{% endfor %}

-- Resume the tasks to start processing
{% for task in stage_config.tasks %}
ALTER TASK {{ task.name }} RESUME;
{% endfor %}
