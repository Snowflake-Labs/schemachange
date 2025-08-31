
{% from 'modules/create_file_format.j2' import create_file_format %}

{% set test_format = {
    "name": "TEST_CSV",
    "type": "CSV",
    "compression": "AUTO",
    "field_delimiter": ",",
    "skip_header": 0
} %}

{{ create_file_format(test_format) }}
