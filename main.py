import time

import cold_pipeline
import prediction
import scheduler


def run_service(delay_seconds: int = 10):
    print("TempSched+ started")
    while True:
        scan_cycle = cold_pipeline.process_files()
        actions = scheduler.schedule()
        future = prediction.predict(scheduler.snapshot()["temperature_store"])
        print("Scan/compression cycle:", scan_cycle)
        print("Scheduling actions:", actions)
        print("Predicted temperature:", future)
        time.sleep(delay_seconds)


if __name__ == "__main__":
    run_service()
