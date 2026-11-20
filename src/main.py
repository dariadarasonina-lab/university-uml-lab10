"""Консольный интерфейс университетской информационной системы."""

from datetime import date

from university import AdministrativeEmployee, Course, Faculty, Institute, Project, University


def create_university() -> University:
    dean = AdministrativeEmployee("ADM-01", "Анна Орлова", "dean@example.test")
    institute = Institute("Кафедра программирования", "Университетская пл., 1")
    mathematics = Institute("Кафедра дискретной математики", "Университетская пл., 1")
    physics = Institute("Кафедра общей физики", "Университетская пл., 2")
    physics_dean = AdministrativeEmployee("ADM-02", "Игорь Лебедев", "physics@example.test")
    computer_science = Faculty(
        "Факультет компьютерных наук",
        {unit.name: unit for unit in (institute, mathematics)},
        dean,
    )
    physics_faculty = Faculty("Физический факультет", {physics.name: physics}, physics_dean)
    project = Project("Цифровой кампус", date(2026, 9, 1), date(2027, 5, 31))
    course = Course(101, "Объектно-ориентированное проектирование", 4)
    return University(
        "ВГУ",
        {faculty.name: faculty for faculty in (computer_science, physics_faculty)},
        {employee.ssn: employee for employee in (dean, physics_dean)},
        {project.name: project},
        {course.number: course},
    )


def ask(prompt: str) -> str:
    return input(prompt).strip()


def register(university: University) -> None:
    code = ask("Социальный код: ")
    name = ask("Имя: ")
    email = ask("Электронная почта: ")
    area = ask("Область исследований: ")
    institutes = ask("Кафедры (через запятую): ")
    lecturer = ask("Преподаватель [да/нет]: ").lower()
    if lecturer not in {"да", "нет"}:
        raise ValueError("Введите «да» или «нет».")
    names = tuple(name.strip() for name in institutes.split(",") if name.strip())
    researcher = university.register_researcher(code, name, email, area, names, lecturer == "да")
    print(f"Сотрудник зарегистрирован: {researcher.name} ({researcher.ssn}).")


def assign_project(university: University) -> None:
    print("Проекты: " + ", ".join(university.projects))
    code = ask("Социальный код: ")
    name = ask("Название проекта: ")
    hours = int(ask("Часы участия: "))
    participation = university.assign_project(code, name, hours)
    print(f"Участие сохранено: {participation.project.name} · {participation.hours} ч.")


def assign_course(university: University) -> None:
    print("Курсы: " + ", ".join(f"{course.number} · {course.name}" for course in university.courses.values()))
    code = ask("Социальный код: ")
    number = int(ask("Номер курса: "))
    course = university.assign_course(code, number)
    print(f"Курс закреплён: № {course.number} · {course.weekly_duration} ч/нед.")


def main() -> None:
    university = create_university()
    print("Университетская информационная система")
    print("1 · Структура и численность   2 · Регистрация сотрудника")
    print("3 · Участие в проекте         4 · Закрепление курса")
    print("5 · Нагрузка сотрудника       0 · Выход")
    while True:
        try:
            command = ask("\nДействие: ")
            if command == "0":
                return
            if command == "1":
                print(university.overview())
            elif command == "2":
                register(university)
            elif command == "3":
                assign_project(university)
            elif command == "4":
                assign_course(university)
            elif command == "5":
                print(university.workload(ask("Социальный код: ")))
            else:
                print("Выберите действие от 0 до 5.")
        except ValueError as error:
            print(f"Ошибка: {error}")
        except (EOFError, KeyboardInterrupt):
            return


if __name__ == "__main__":
    main()
