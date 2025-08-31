{% from 'modules/task_operations.j2' import create_task %}
{% from '2_test/stages_legacy.j2' import stage_config %}
{% from '2_test/trips_legacy.j2' import trips_definitions %}
{% from '2_test/weather_legacy.j2' import weather_definitions %}

-- LEGACY APPROACH: Without LocalDataInjection - manual data definitions in Jinja
-- This shows the "before" state that LocalDataInjection improves upon
-- Instead of using from_yaml('stages.yaml'), we manually define the data structure
-- in stages_legacy.j2 and import it

-- Convert tuples to dictionaries (same as from_csv() would do)
{% set trips_definitions_dict = [] %}
{% for row in trips_definitions %}
    {% set _ = trips_definitions_dict.append({
        'column_name': row[0],
        'data_type': row[1],
        'nullable': row[2],
        'description': row[3],
        'source_column': row[4],
        'landing_transformation': row[5],
        'final_transformation': row[6]
    }) %}
{% endfor %}

{% set weather_definitions_dict = [] %}
{% for row in weather_definitions %}
    {% set _ = weather_definitions_dict.append({
        'column_name': row[0],
        'data_type': row[1],
        'nullable': row[2],
        'description': row[3],
        'source_column': row[4],
        'landing_transformation': row[5],
        'final_transformation': row[6]
    }) %}
{% endfor %}

-- Set the database and schema context
USE SCHEMA {{database_name}}.{{schema_name}};

-- Create tasks for processing data from landing to final tables using the SAME macros as LocalDataInjection version
{% for task in stage_config.tasks %}
    {% if task.name == 'PROCESS_TRIPS_DATA' %}
        {{ create_task(task, trips_definitions_dict) }}
    {% elif task.name == 'PROCESS_WEATHER_DATA' %}
        {{ create_task(task, weather_definitions_dict) }}
    {% endif %}
{% endfor %}

-- Resume the tasks to start processing
{% for task in stage_config.tasks %}
ALTER TASK {{ task.name }} RESUME;
{% endfor %}
