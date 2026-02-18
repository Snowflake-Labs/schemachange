{% from 'modules/create_stage.j2' import create_stage %}
{% from 'modules/table_operations.j2' import create_table, create_view %}
{% from 'modules/create_file_format.j2' import create_file_format %}

-- Load data from external files using LocalDataInjection
{% set trips_definitions = from_csv('2_test/trips.csv', as_dict=true) %}
{% set weather_definitions = from_csv('2_test/weather.csv', as_dict=true) %}
{% set file_format_config = from_json('2_test/file_formats.json') %}
{% set stage_config = from_yaml('2_test/stages.yaml') %}

-- Create the database if it doesn't exist
USE DATABASE {{database_name}};

-- Set the database and schema context
USE SCHEMA {{database_name}}.{{schema_name}};

-- Create file formats from JSON configuration
{% for file_format in file_format_config.file_formats %}
{{ create_file_format(file_format) }}
{% endfor %}

-- Create stages from YAML configuration
{% for stage in stage_config.stages %}
{{ create_stage(stage.name, stage.url) }}
{% endfor %}

-- Create landing tables (all VARCHAR with metadata) from CSV configuration
{{ create_table('TRIPS', trips_definitions, as_varchar=true) }}
{{ create_table('WEATHER', weather_definitions, as_varchar=true) }}

-- Create final tables from CSV configuration
{{ create_table('TRIPS', trips_definitions) }}
{{ create_table('WEATHER', weather_definitions) }}

-- Create views that filter to latest data and apply transformations
{{ create_view('TRIPS_VIEW', 'TRIPS_LANDING', trips_definitions) }}
{{ create_view('WEATHER_VIEW', 'WEATHER_LANDING', weather_definitions) }}
