# pipeline/flyte/workflow.py
from flytekit import workflow
from pipeline.flyte.tasks import etl_refresh, forecast_to_gold, optimize_to_gold

@workflow
def nightly() -> bool:
    etl_ok = etl_refresh()
    fc_ok  = forecast_to_gold()
    opt_ok = optimize_to_gold()
    return etl_ok and fc_ok and opt_ok

if __name__ == "__main__":
    # simple local entrypoint
    nightly()
