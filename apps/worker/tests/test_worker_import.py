from apps.worker.app.main import worker_name


def test_worker_name() -> None:
    assert worker_name() == "ResearchOS Worker"
