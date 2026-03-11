# Session tracking notes for group project in Dataplatform Development

## Thursday 05/03-2026
**Goals for today:**
```text
- Wrote and generated fake data
    - Done
- Refactored generator.py script to include more data points messured
    - Done
```


## Saturday 07/03-2026
**Goals for today:**
```text
- Update generator.py name to producer.py
    - Done

- Add some kind of 'fleet system' to be able to track usage over time for each sensor.
    - Done

- Add function for format_noise and category_noise in generated data for group to clean in silver layer with pandas/etl script.
    - Done

- Add module overview docs for producer.py(me) + consumer.py(Indira)
    - Done

- Add visual ERDs(CDM,LDM,PDM) for bronze layer
    - Done

- Create rough datamodeling drafts of ERD for silver layer 
    - Done
```

## Sunday 08/03-2026
```text
- Refactored producer.py to let it generate more chaos and faulty values instead of just RPM. Now includes: "rpm", "engine_temp", "vibration_hz", "run_hours" instead of just rpm.
    - Done
```

## Monday 09/03-2026
**Goals for today:**
```text
- Hold stand up meeting
    - Done

- Generate new data for db with improved params
    - Done
```

## Wednesday 11/03-2026
**Goals for today:**
```text
- Update random hours run generation from 5000 to 500. Unreasonably high to expect first sensor appearance to be able to show 5k hours.
    - Done

- Updated docs folder with brief docs on how to sync your postgres DB to contain the same data as everyone elses. Brief run guide on how to use the replayer.py script
    - Done

- Add silver layer ERDs + gold layer ERDs
    - Ongoing

```