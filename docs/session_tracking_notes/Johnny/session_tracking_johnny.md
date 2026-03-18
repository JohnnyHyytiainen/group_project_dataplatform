# Session tracking notes for group project in Dataplatform Development

## Thursday 05/03-2026
**Goals for today:**

- Wrote and generated fake data
    - **Done**
- Refactored generator.py script to include more data points messured
    - **Done**



## Saturday 07/03-2026
**Goals for today:**

- Update generator.py name to producer.py
    - **Done**

- Add some kind of 'fleet system' to be able to track usage over time for each sensor.
    - **Done**

- Add function for format_noise and category_noise in generated data for group to clean in silver layer with pandas/etl script.
    - **Done**

- Add module overview docs for producer.py(me) + consumer.py(Indira)
    - **Done**

- Add visual ERDs(CDM,LDM,PDM) for bronze layer
    - **Done**

- Create rough datamodeling drafts of ERD for silver layer 
    - **Done**


## Sunday 08/03-2026

- Refactored producer.py to let it generate more chaos and faulty values instead of just RPM. Now includes: "rpm", "engine_temp", "vibration_hz", "run_hours" instead of just rpm.
    - **Done**


## Monday 09/03-2026
**Goals for today:**

- Hold stand up meeting
    - **Done**

- Generate new data for db with improved params
    - **Done**


## Wednesday 11/03-2026
**Goals for today:**

- Update random hours run generation from 5000 to 500. Unreasonably high to expect first sensor appearance to be able to show 5k hours.
    - **Done**

- Updated docs folder with brief docs on how to sync your postgres DB to contain the same data as everyone elses. Brief run guide on how to use the replayer.py script
    - **Done**

- Add silver layer ERDs + gold layer ERDs
    - **Done**


## Thursday 12/03-2026
**Goals for today:**
- Update entire workflow architecture for silver layer in mermaid.
    - **Done**

- Hold stand-up and explain architecture choices. Emphasis on idempotency, being able to run scripts over and over and over again.
    - **Done**

- Show templates on silver layer scripts, explain most important rows that CANNOT be changed. Rest can be changed how ever coder seems fit.
    - **Done**

- Plan for user stories and workload for silver.
    - **Done**

- Add dependency for psycopg-pool with - uv add psycopg-pool
    - **Done**

Add database connection pool for API
    - **Done**

- Start working on basic API endpoints 
    - **Done**

- Write module overview docs for API and connection pooling (docs/module_overview_api_core.md)
    - **Done**


## Saturday 14/03-2026
**Goals for today:**

- Refactor get_db_connection(): function in db_conn_pool script. Faulty logic needs fixing.
- Issue: Trying to YIELD from within a with statement. With psycopg_pool it is better and safer to ask the pool for a connection directly, otherwise FastAPI may have problems closing the connection asynchronously.

    - *Refactored for safety. Now gets connection manually with a "stricter" try/finally block of code.*
        - **Done**

- Refactor and update main.py, specifically /api/vi/sensors endpoint for better error handling.
- Issue: Did not have any way of logging errors for troubleshooting. Updated main.py /api/vi/sensors endpoint to contain an error logger. -> Improves future troubleshooting with endpoint.
    - *Refactored for easier troubleshooting(Thank you Johnny from the past. /// Future Johnny)*
        - **Done**


- Update documentation for bronze module overview. Now contains: Complete module overview that includes:
    * Producer script
    * Consumer script
    * Replayer script
    * db_config script
    * sensor_schema script
        - Done
        

## Sunday 15/03-2026
**Goals for today:**
- Setup docker-compose, Dockerfile and containerize EVERYTHING.
    - producer
    - consumer
    - kafka
    - postgres db
    - api
        - **DONE**

- Written small module overview for orchestration with docker.
    - **DONE**

    
## Monday 16/03-2026
**Goals for today:**
- Get entire orchestration working with docker-compose. Changed config in replayer script, added it to container and now it works as intended. See [Overview](../../module_overview_orchestration.md) docs for explanations.
    - **DONE**

- Wrote docs on how to update entire DB with new files from replayer.
    - **Done**

- Added sandbox scripts to feat/pair_programming branch together with Indira
    - **Done**

- Setup for everyone to run the same docker environment in the group.
    - **Done**

- Database design overview added in docs.
    - **Done**

## Wednesday 18/03-2026
**Goals for today:**
- Setup and test CI/CD pipeline with github actions to test our code automatically at every push or pull request.
    - Ongoing

- Refactor main.py and add + test query params to filter for the only data user would want to have.
    - Ongoing

- Write module docs for entire api module + module docs for CI/CD pipeline.
    - Ongoing