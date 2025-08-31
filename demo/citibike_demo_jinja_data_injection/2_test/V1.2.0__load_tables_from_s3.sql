{% from 'modules/table_operations.j2' import copy_into_landing %}

-- Load configuration from YAML file using LocalDataInjection
{% set stage_config = from_yaml('2_test/stages.yaml') %}
{% set trips_definitions = from_csv('2_test/trips.csv', as_dict=true) %}
{% set weather_definitions = from_csv('2_test/weather.csv', as_dict=true) %}

-- Set the database and schema context
USE SCHEMA {{database_name}}.{{schema_name}};

-- Load data into landing tables using copy operations defined in YAML
{% for operation_name, operation in stage_config.copy_operations.items() %}
    {% if operation.table == 'TRIPS_LANDING' %}
        {{ copy_into_landing(operation, trips_definitions) }}
    {% elif operation.table == 'WEATHER_LANDING' %}
        {{ copy_into_landing(operation, weather_definitions) }}
    {% endif %}
{% endfor %}
