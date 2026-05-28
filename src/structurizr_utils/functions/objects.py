from datetime import datetime
from typing import TypedDict, Optional ,Dict, List
import logging

# результат проверок

class AssessmentObjects(TypedDict):
    isCheck : bool
    details : List[Dict[str,str]]

    def __init__(self, isCheck: bool, details: List[Dict[str,str]]) -> None:
        super().__init__()
        self.isCheck = isCheck
        self.details = details

class FitnessStatus(TypedDict):
    code : str
    isCheck : bool
    resultDetails : Optional[str]
    assessmentDescription : Optional[str]
    assessmentObjects : Optional[List[AssessmentObjects]]

    # Init class
    def __init__(
        self,
        code: str,
        isCheck: bool,
        resultDetails: Optional[str] = None,
        assessmentDescription: Optional[str] = None,
        assessmentObjects: Optional[List[AssessmentObjects]] = None
    ):
        self.code = code
        self.isCheck = isCheck
        self.resultDetails = resultDetails
        self.assessmentDescription = assessmentDescription
        self.assessmentObjects = assessmentObjects


# проверка
class Assessment(TypedDict):
    code : str
    description : str

    def __init__(self, code:str, description: str) -> None:
        self.code = code
        self.description = description


def safe_execution(func, *args, **kwargs) -> list[FitnessStatus]:
    """
    Функция для безопасного выполнения переданной функции с обработкой исключений.
    :param func: функция, которую нужно выполнить
    :param args: позиционные аргументы для func
    :param kwargs: именованные аргументы для func
    :return: результат выполнения func или сообщение об ошибке
    """
    try:
        # Выполняем переданную функцию с переданными аргументами
        return func(*args, **kwargs)
    except Exception as e:
        # Обрабатываем исключение
        logging.error(f"\u001b[31m# Произошла ошибка: {e}\u001b[37m")
        return list()