# Citibike Demo with LocalDataInjection

This demo showcases the `LocalDataInjection` functionality in schemachange, which extends Jinja templates with the ability to load data from external files (CSV, JSON, YAML) directly into templates.

## Features Demonstrated

- **Data Injection Pattern**: Externalize table definitions, file formats, and configuration from SQL into data files
- **Co-located Data Files**: Data files are placed alongside the SQL files that use them for better organization
- **Consolidated Macros**: DRY (Don't Repeat Yourself) approach with reusable macros
- **Data Pipeline Pattern**: Landing tables (VARCHAR) → Views (filtered/transformed) → Final tables (typed)
- **Snowflake Metadata**: Proper use of `METADATA$` functions and `OBJECT_CONSTRUCT`
- **Before/After Comparison**: Legacy hardcoded approach vs. data injection approach

## File Structure

```
citibike_demo_jinja_data_injection/
├── 2_test/
│   ├── trips.csv                    # TRIPS table definition
│   ├── weather.csv                  # WEATHER table definition
│   ├── file_formats.json            # File format configurations
│   ├── stages.yaml                  # Stage and task configurations
│   ├── V1.1.0__initial_database_objects.sql
│   ├── V1.1.0__initial_database_objects_legacy.sql
│   ├── V1.2.0__load_tables_from_s3.sql
│   ├── V1.2.0__load_tables_from_s3_legacy.sql
│   ├── V1.3.0__create_tasks.sql
│   └── V1.3.0__create_tasks_legacy.sql
├── 3_teardown/
│   └── A__teardown.sql
├── modules/
│   ├── table_operations.j2          # Consolidated table/view/copy macros
│   ├── table_operations_legacy.j2   # Legacy hardcoded macros
│   ├── legacy_data_definitions.j2   # Manual tuple definitions (legacy approach)
│   ├── task_operations.j2           # Task creation macros
│   ├── config_example.j2            # Example of {% with context %} usage
│   ├── create_stage.j2              # Stage creation macro
│   └── create_file_format.j2        # File format creation macro
└── README.md
```

## Data Files

### trips.csv
Defines the column structure for the `TRIPS` table with transformation logic:
- `column_name`: Column identifier
- `data_type`: Target data type for final table
- `nullable`: NULL constraint
- `description`: Column description
- `source_column`: Source column reference ($1, $2, etc.)
- `landing_transformation`: Transformation for landing table (VARCHAR)
- `final_transformation`: Transformation for final table (typed)

### weather.csv
Similar structure for the `WEATHER` table with JSON-specific transformations.

### file_formats.json
JSON configuration for Snowflake file formats:
```json
{
  "file_formats": [
    {
      "name": "CSV_NO_HEADER",
      "type": "CSV",
      "compression": "AUTO",
      "field_delimiter": ",",
      "skip_header": 0,
      "field_optionally_enclosed_by": "\"",
      "null_if": ["NULL", "\\N", "\\N", ""]
    },
    {
      "name": "JSON",
      "type": "JSON",
      "compression": "AUTO"
    }
  ]
}
```

### stages.yaml
YAML configuration for stages, copy operations, and tasks:
```yaml
stages:
  - name: TRIPS
    url: "{{ secrets.trips_s3_bucket }}"
  - name: WEATHER
    url: "{{ secrets.weather_s3_bucket }}"

copy_operations:
  trips_landing:
    table: TRIPS_LANDING
    stage: TRIPS
    file_format: CSV_NO_HEADER
    pattern: ".*trips_.*csv.gz"

tasks:
  - name: PROCESS_TRIPS_DATA
    warehouse: "{{ database_name }}_WH"
    schedule: "USING CRON '0 */6 * * * UTC'"
```

## Consolidated Macros

### table_operations.j2
Contains three main macros:

1. **`create_table(table_name, columns, as_varchar=false)`**
   - Creates landing tables (all VARCHAR) or final tables (typed)
   - Automatically adds METADATA and LOAD_TIME columns

2. **`create_view(view_name, source_table, table_definitions)`**
   - Creates views that filter to latest data and apply transformations
   - Uses `final_transformation` from CSV definitions

3. **`copy_into_landing(operation, table_definitions)`**
   - Loads data into landing tables with metadata
   - Uses `landing_transformation` from CSV definitions
   - Supports optional pattern matching

### task_operations.j2
Contains task creation macros that generate SQL for processing data from landing to final tables.

## Data Pipeline Flow

1. **Landing Tables**: All columns as VARCHAR, includes metadata and load timestamp
2. **Views**: Filter to latest data, apply type casting and transformations
3. **Final Tables**: Properly typed data ready for analysis
4. **Tasks**: Automated processing on schedule

## {% with context %} Usage

The demo includes `config_example.j2` to demonstrate proper usage of `{% with context %}`:

**Good Practice**: Pass variables explicitly to macros
```jinja
{% from 'modules/config_example.j2' import good_macro %}
{{ good_macro(database_name, schema_name) }}
```

**Bad Practice**: Use config variables directly in macros (requires `{% with context %}`)
```jinja
{% from 'modules/config_example.j2' import bad_macro with context %}
{{ bad_macro() }}
```

## Benefits of LocalDataInjection

### Before (Legacy)
- **Manual Tuple Definitions**: Long arrays of tuples manually defined in J2 files
- **Import Approach**: `{% from 'modules/legacy_data_definitions.j2' import trips_definitions %}`
- **Hardcoded Macros**: Macros must be modified for any table structure changes
- **Difficult Maintenance**: Editing raw data requires manually updating tuple arrays
- **No Flexibility**: Each table requires its own hardcoded macro logic

**Example Legacy Approach:**
```jinja
-- In legacy_data_definitions.j2
{% set trips_definitions = [
    ('TRIPDURATION', 'INTEGER', 'NOT NULL', 'Trip duration in seconds', '$1', '$1', 'CAST(TRIPDURATION AS INTEGER)'),
    ('STARTTIME', 'TIMESTAMP', 'NOT NULL', 'Start time of the trip', '$2', '$2', 'CAST(STARTTIME AS TIMESTAMP)'),
    -- ... 16 more manually defined tuples
] %}

-- In SQL file
{% from 'modules/legacy_data_definitions.j2' import trips_definitions %}
```

### After (LocalDataInjection)
- **External Data Files**: Clean CSV/JSON/YAML files with structured data
- **Simple Function Calls**: `{% set trips_definitions = from_csv('trips.csv', as_dict=true) %}`
- **Flexible Macros**: Same macros work with any table structure
- **Easy Maintenance**: Edit data files directly, no manual tuple creation
- **Reusable**: Single definition used across multiple contexts

**Example LocalDataInjection Approach:**
```jinja
-- In trips.csv (easy to edit)
column_name,data_type,nullable,description,source_column,landing_transformation,final_transformation
TRIPDURATION,INTEGER,NOT NULL,Trip duration in seconds,$1,$1,CAST(TRIPDURATION AS INTEGER)
STARTTIME,TIMESTAMP,NOT NULL,Start time of the trip,$2,$2,CAST(STARTTIME AS TIMESTAMP)

-- In SQL file (simple and clean)
{% set trips_definitions = from_csv('trips.csv', as_dict=true) %}
```

## Testing

All SQL files have been tested and render successfully:
- ✅ `V1.1.0__initial_database_objects.sql` (LocalDataInjection version)
- ✅ `V1.1.0__initial_database_objects_legacy.sql` (Legacy version)
- ✅ `V1.2.0__load_tables_from_s3.sql` (LocalDataInjection version)
- ✅ `V1.2.0__load_tables_from_s3_legacy.sql` (Legacy version)
- ✅ `V1.3.0__create_tasks.sql` (LocalDataInjection version)
- ✅ `V1.3.0__create_tasks_legacy.sql` (Legacy version)
- ✅ `A__teardown.sql`

## Usage

1. Set up your Snowflake environment
2. Configure your `schemachange.yaml` with appropriate variables
3. Run the migration files in order:
   ```bash
   schemachange -f 2_test/ -v
   ```
4. Clean up with the teardown script:
   ```bash
   schemachange -f 3_teardown/ -v
   ```

## Key Learnings

- **Co-location**: Data files should be placed alongside the SQL files that use them
- **Dictionary Access**: When loading from JSON/YAML, use dictionary access (`['key']`) not attribute access (`.key`)
- **Optional Fields**: Use `is defined` checks for optional configuration fields
- **DRY Principle**: Consolidate macros to avoid duplication
- **Explicit Variables**: Pass variables explicitly to macros rather than relying on `{% with context %}`
- **Ergonomic Benefits**: LocalDataInjection eliminates the need for manual tuple creation and makes data editing much easier
