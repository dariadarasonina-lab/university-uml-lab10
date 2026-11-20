from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Employee:
    """{abstract}"""
    ssn: str
    name: str
    email: str

    def __post_init__(self) -> None:
        if type(self) is Employee:
            raise TypeError("Укажите категорию сотрудника.")


@dataclass
class AdministrativeEmployee(Employee):
    pass


@dataclass
class Researcher(Employee):
    research_area: str
    institutes: tuple[Institute, ...]  # uml: 0..* --> 1..* Institute
    participations: dict[str, Participation] = field(default_factory=dict)  # uml: 1 *-- 0..* Participation

    def __post_init__(self) -> None:
        if not self.institutes:
            raise ValueError("У научного сотрудника должна быть хотя бы одна кафедра.")

    def assign_project(self, project: Project, hours: int) -> Participation:
        if project.name in self.participations:
            raise ValueError("Сотрудник уже участвует в этом проекте.")
        participation = Participation(project, hours)
        self.participations[project.name] = participation
        return participation


@dataclass
class Lecturer(Researcher):
    courses: dict[int, Course] = field(default_factory=dict)  # uml: 0..* --> 0..* Course

    def assign_course(self, course: Course) -> None:
        if course.number in self.courses:
            raise ValueError("Этот курс уже закреплён за преподавателем.")
        self.courses[course.number] = course


@dataclass
class Institute:
    name: str
    address: str


@dataclass
class Faculty:
    name: str
    institutes: dict[str, Institute]  # uml: 1 *-- 1..* Institute
    dean: Employee  # uml: 0..* --> 1 Employee

    def __post_init__(self) -> None:
        if not self.institutes:
            raise ValueError("На факультете должна быть хотя бы одна кафедра.")


@dataclass
class Project:
    name: str
    starting_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.starting_date:
            raise ValueError("Дата окончания проекта предшествует дате начала.")


@dataclass
class Participation:
    project: Project  # uml: 0..* --> 1 Project
    hours: int

    def __post_init__(self) -> None:
        if self.hours <= 0:
            raise ValueError("Число часов участия должно быть положительным.")


@dataclass
class Course:
    number: int
    name: str
    weekly_duration: int

    def __post_init__(self) -> None:
        if self.number <= 0 or self.weekly_duration <= 0:
            raise ValueError("Номер курса и недельная нагрузка должны быть положительными.")


@dataclass
class University:
    name: str
    faculties: dict[str, Faculty]  # uml: 1 *-- 1..* Faculty
    employees: dict[str, Employee]  # uml: 1 o-- 1..* Employee
    projects: dict[str, Project]  # uml: 1 o-- 0..* Project
    courses: dict[int, Course]  # uml: 1 o-- 0..* Course

    def __post_init__(self) -> None:
        if not self.faculties:
            raise ValueError("У университета должен быть хотя бы один факультет.")
        institute_names = set()
        for faculty in self.faculties.values():
            if self.employees.get(faculty.dean.ssn) is not faculty.dean:
                raise ValueError("Декан должен числиться в штате университета.")
            if institute_names.intersection(faculty.institutes):
                raise ValueError("Названия кафедр в справочнике должны быть уникальными.")
            institute_names.update(faculty.institutes)

    def employee_count(self) -> int:
        return len(self.employees)

    def overview(self) -> str:
        lines = [f"{self.name}. Всего сотрудников: {self.employee_count()}"]
        for faculty in self.faculties.values():
            lines.append(f"{faculty.name}. Декан: {faculty.dean.name}")
            lines.extend(f"  {unit.name} · {unit.address}" for unit in faculty.institutes.values())
        return "\n".join(lines)

    def register_researcher(
        self, ssn: str, name: str, email: str, research_area: str,
        institute_names: tuple[str, ...], lecturer: bool,
    ) -> Researcher:
        if not all((ssn.strip(), name.strip(), research_area.strip())):
            raise ValueError("Код, имя и область исследований обязательны.")
        if ssn in self.employees:
            raise ValueError("Сотрудник с таким социальным кодом уже зарегистрирован.")
        local, separator, domain = email.partition("@")
        if not local or not separator or not domain or "@" in domain or any(c.isspace() for c in email):
            raise ValueError("Укажите электронный адрес в формате имя@домен.")
        institutes = {
            key: unit for faculty in self.faculties.values()
            for key, unit in faculty.institutes.items()
        }
        try:
            selected = tuple(institutes[key] for key in dict.fromkeys(institute_names))
        except KeyError as error:
            raise ValueError(f"Кафедра «{error.args[0]}» отсутствует в справочнике.") from None
        employee_type = Lecturer if lecturer else Researcher
        researcher = employee_type(ssn, name, email, research_area, selected)
        self.employees[ssn] = researcher
        return researcher

    def assign_project(self, ssn: str, project_name: str, hours: int) -> Participation:
        researcher = self._researcher(ssn)
        project = self.projects.get(project_name)
        if project is None:
            raise ValueError("Проект отсутствует в справочнике.")
        return researcher.assign_project(project, hours)

    def assign_course(self, ssn: str, course_number: int) -> Course:
        lecturer = self._researcher(ssn)
        if not isinstance(lecturer, Lecturer):
            raise ValueError("Курс можно закрепить только за преподавателем.")
        course = self.courses.get(course_number)
        if course is None:
            raise ValueError("Курс с таким номером отсутствует в справочнике.")
        lecturer.assign_course(course)
        return course

    def workload(self, ssn: str) -> str:
        researcher = self._researcher(ssn)
        institutes = ", ".join(unit.name for unit in researcher.institutes)
        lines = [f"{researcher.name} · {researcher.research_area}", f"Кафедры: {institutes}"]
        if researcher.participations:
            lines.append("Участие в проектах")
            for item in researcher.participations.values():
                project = item.project
                lines.append(f"  {project.name}: {item.hours} ч · {project.starting_date} — {project.end_date}")
        else:
            lines.append("Участие в проектах отсутствует.")
        if isinstance(researcher, Lecturer) and researcher.courses:
            lines.append("Учебные курсы")
            for course in researcher.courses.values():
                lines.append(f"  № {course.number} · {course.name}: {course.weekly_duration} ч/нед.")
        else:
            lines.append("Учебные курсы отсутствуют.")
        return "\n".join(lines)

    def _researcher(self, ssn: str) -> Researcher:
        employee = self.employees.get(ssn)
        if not isinstance(employee, Researcher):
            raise ValueError("Научный сотрудник с таким кодом не найден.")
        return employee
