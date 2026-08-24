import time


def worker_name() -> str:
    return "ResearchOS Worker"


def run_forever() -> None:
    while True:
        time.sleep(60)


if __name__ == "__main__":
    run_forever()
