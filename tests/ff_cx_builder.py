"""Общий билдер workspace для тестов CX.01–CX.03 (по модели, без views).

Не является тестовым модулем (pytest его не собирает) — только helper.
"""

from __future__ import annotations

from typing import Any, Dict


def make_cx_workspace(
    *,
    person_relationship: bool = True,
    person_relation_destination: str = "2",
    container_tech: str = "React, TypeScript, JavaScript",
    system_cmdb: str = "FDMSHOWCASEAPP",
    with_tc: bool = True,
) -> Dict[str, Any]:
    """Workspace в формате Structurizr JSON: Person + одна система с одним контейнером.

    Args:
        person_relationship: добавить связь ``person -> destination`` (признак UI).
        person_relation_destination: id цели связи Person ("2" — контейнер, "1" — система).
        container_tech: строка ``technology`` контейнера.
        system_cmdb: значение ``properties.cmdb`` целевой системы.
        with_tc: добавить в контейнер component ``type=capability`` (TC для CX.03).
    """
    person: Dict[str, Any] = {
        "id": "10",
        "name": "Пользователь",
        "description": "Пользователь системы",
        "tags": "Person",
        "relationships": [
            {
                "id": "r1",
                "description": "Использует интерфейс",
                "technology": "HTTPS:443",
                "destinationId": person_relation_destination,
            }
        ]
        if person_relationship
        else [],
    }

    container: Dict[str, Any] = {
        "id": "2",
        "name": "Web интерфейс",
        "description": "Пользовательский интерфейс",
        "technology": container_tech,
        "tags": "frontend",
        "relationships": [],
        "components": [
            {
                "id": "c1",
                "name": "UI TC",
                "description": "Описание TC",
                "properties": {
                    "type": "capability",
                    "code": "0001",
                    "parents": "DMN.044",
                },
            }
        ]
        if with_tc
        else [],
    }

    system: Dict[str, Any] = {
        "id": "1",
        "name": "BEEATLAS",
        "description": "Система",
        "tags": "Software System",
        "properties": {"cmdb": system_cmdb, "modified": "2026-08-01"},
        "relationships": [],
        "containers": [container],
    }

    return {
        "configuration": {},
        "model": {
            "properties": {"workspace_cmdb": "fdmshowcaseapp"},
            "people": [person],
            "softwareSystems": [system],
        },
        "views": {"systemContextViews": [], "containerViews": []},
    }
