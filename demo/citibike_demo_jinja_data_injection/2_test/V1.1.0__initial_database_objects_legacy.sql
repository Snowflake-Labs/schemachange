{% from 'modules/create_stage.j2' import create_stage %}
{% from 'modules/table_operations.j2' import create_table, create_view %}
{% from 'modules/create_file_format.j2' import create_file_format %}
{% from '2_test/trips_legacy.j2' import trips_definitions %}
{% from '2_test/weather_legacy.j2' import weather_definitions %}
{% from '2_test/file_formats_legacy.j2' import file_format_config %}
{% from '2_test/stages_legacy.j2' import stage_config %}

-- LEGACY APPROACH: Without LocalDataInjection - manual data definitions in Jinja
-- This shows the "before" state that LocalDataInjection improves upon
-- Instead of using from_csv('trips.csv', as_dict=true), we manually define the data structure
-- in trips_legacy.j2 and import it with: from '2_test/trips_legacy.j2' import trips_definitions

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

-- Create the database if it doesn't exist
USE DATABASE {{database_name}};

-- Set the database and schema context
USE SCHEMA {{database_name}}.{{schema_name}};

-- Create file formats from hardcoded configuration
{% for file_format in file_format_config.file_formats %}
{{ create_file_format(file_format) }}
{% endfor %}

-- Create stages from hardcoded configuration
{% for stage in stage_config.stages %}
{{ create_stage(stage.name, stage.url) }}
{% endfor %}

-- Create landing tables using the SAME macros as LocalDataInjection version
{{ create_table('TRIPS', trips_definitions_dict, as_varchar=true) }}
{{ create_table('WEATHER', weather_definitions_dict, as_varchar=true) }}

-- Create final tables using the SAME macros as LocalDataInjection version
{{ create_table('TRIPS', trips_definitions_dict) }}
{{ create_table('WEATHER', weather_definitions_dict) }}

-- Create views using the SAME macros as LocalDataInjection version
{{ create_view('TRIPS_VIEW', 'TRIPS_LANDING', trips_definitions_dict) }}
{{ create_view('WEATHER_VIEW', 'WEATHER_LANDING', weather_definitions_dict) }}
