# HOW TO RUN CLI COMMANDS


## Run the pipeline runner (remote(fjärrkontrollen))

- Open a terminal
1) To only clean new data(silver):
    - `uv run python -m src.pipeline_runner --layer silver`

2) To only update dashboard(gold):
    - `uv run python -m src.pipeline_runner --layer gold`

3) To run EVERYTHING(ALL NIGHT BATCH)
    - `uv run python -m src.pipeline_runner --layer all`

4) To run DAILY AGGREGATION(gold):
    - `uv run python -m src.pipeline_runner --layer daily`