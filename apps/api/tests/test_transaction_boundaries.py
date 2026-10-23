import inspect
from typing import get_args, get_type_hints

from apps.api.app.api import dependencies
from apps.api.app.api.dependencies import get_db_session
from apps.api.app.api.routers import chat, files, jobs, projects


def test_database_transactions_finish_before_responses_are_sent() -> None:
    database_dependencies = []

    for module in (dependencies, chat, files, jobs, projects):
        for function_name, function in inspect.getmembers(module, inspect.isfunction):
            if function.__module__ != module.__name__:
                continue
            for annotation in get_type_hints(function, include_extras=True).values():
                for metadata in get_args(annotation)[1:]:
                    if getattr(metadata, "dependency", None) is get_db_session:
                        database_dependencies.append(
                            (f"{module.__name__}.{function_name}", metadata)
                        )

    assert database_dependencies
    assert [
        name for name, dependency in database_dependencies if dependency.scope != "function"
    ] == []
