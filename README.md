# snowchange
Snowchange is a simple python script which helps manage schema changes for the [Snowflake](https://www.snowflake.com/) data warehouse.

When combined with a version control system and a CI/CD tool, schema changes can be approved and deployed through a pipeline using modern software delivery practises.

## Usage

It's just a single python file named [snowchange.py](snowchange.py). Create your own repository, copy it in there, and follow the example databases structure to get started.

### Preparation

The function expects a directory structure like the following to exist:
```
(rootFolder)
 |
 |-> databases
      |-> database1
           |->schema1
           |   |-> 20180825_create_customer_table.sql
           |   |-> 20180826_create_sales_table.sql
           |->schema2
           |   |-> 20180715_create_flights_table.sql
           |   |-> 20180805_create_bookings_table.sql
```

The database name in the directory structure is combined with the environment name, so that a single snowflake  account can include all environments.

Every database will have a table automatically created to track the applying of these change sets.

You will need a user account that has the ```CREATE DATABASE``` account-level permission. 

It is recommended that the script be triggered to run via repository webhooks, however it can safely be re-ran repeatedly.

### Running the script

If your build agent has python 3 installed, the script can be ran like so:
```
pip install --upgrade snowflake-connector-python
python snowchange.py -e $ENVIRONMENT_NAME -a $SNOWFLAKE_ACCOUNT -u $SNOWFLAKE_USER -r $SNOWFLAKE_ROLE -w $SNOWFLAKE_WAREHOUSE --snowflak
e-region $SNOWFLAKE_REGION --repo-revision $GIT_COMMIT_REF
```
it is expected that the environment variable SNOWSQL_PWD be set prior to calling the script, you should make this available to your build agent in some secure fashion.

You'll need to map between the branch name and the target environment name, e.g. 

Or if you prefer docker, set the environment variables and run like so:
```
docker run -it --rm \
  -v "$PWD":/usr/src/snowchange \
  -w /usr/src/snowchange \
  -e SNOWFLAKE_ACCOUNT \
  -e SNOWFLAKE_USER \
  -e SNOWFLAKE_ROLE \
  -e SNOWFLAKE_WAREHOUSE \
  -e SNOWFLAKE_REGION \
  -e SNOWFLAKE_REGION \
  -e SNOWSQL_PWD \
  --name snowchange-script \
  python:3 /bin/bash -c "pip install --upgrade snowflake-connector-python && python snowchange.py -e $ENVIRONMENT_NAME -a $SNOWFLAKE_ACCOUNT -u $SNOWFLAKE_USER -r $SNOWFLAKE_ROLE -w $SNOWFLAKE_WAREHOUSE --snowflake-region $SNOWFLAKE_REGION --repo-revision $BUILDKITE_COMMIT"
```

## The script in context

Here's an example configuration, where pull requests move changes between environments.

![diagram](diagram.png "Diagram")

## Notes

In the interest of safety, if databases/schemas are removed from the repository, they will not automatically be removed in snowflake. The script only giveth, it does not taketh away.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
