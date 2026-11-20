"""Generate a Python skeleton or reverse-engineer the implemented domain model."""

import argparse
import ast
import re
from pathlib import Path


CLASS = re.compile(r"(abstract class|class) (\w+) \{")
MEMBER = re.compile(r"[+-] (.+?): (.+)")
INHERITANCE = re.compile(r"(\w+) <\|-- (\w+)")
RELATION = re.compile(r'(\w+) "([\d.*]+)" (\*--|o--|-->) "([\d.*]+)" (\w+) : (\w+)')
STYLE = """@startuml
title Диаграмма классов · Университетская информационная система
skinparam backgroundColor white
skinparam defaultFontName Arial
skinparam classAttributeIconSize 0
skinparam shadowing false
skinparam dpi 140
hide circle
"""


def split_parameters(value):
    """Split signature parameters while preserving commas in type subscripts."""
    depth = 0
    start = 0
    for index, char in enumerate(value):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        elif char == "," and depth == 0:
            yield value[start:index].strip()
            start = index + 1
    if value[start:].strip():
        yield value[start:].strip()


def forward(source):
    lines = source.splitlines()
    inheritance = {}
    relations = {}
    for line in lines:
        if match := INHERITANCE.fullmatch(line.strip()):
            parent, child = match.groups()
            inheritance[child] = parent
        if match := RELATION.fullmatch(line.strip()):
            owner, left, arrow, right, target, role = match.groups()
            relations[owner, role] = (left, arrow, right, target)
    output = ["from __future__ import annotations\n", "from dataclasses import dataclass, field", "from datetime import date"]
    for line in lines:
        line = line.strip()
        if match := CLASS.fullmatch(line):
            kind, name = match.groups()
            base = f"({inheritance[name]})" if name in inheritance else ""
            output.extend(["\n", "@dataclass", f"class {name}{base}:"])
            if kind == "abstract class":
                output.append('    """{abstract}"""')
            empty = kind == "class"
        elif line == "}" and empty:
            output.append("    pass")
        elif line.startswith(("+ ", "- ")):
            text = line[2:]
            empty = False
            if "(" in text:
                method, _, signature = text.partition("(")
                args, result = signature.rsplit("): ", 1)
                parameters = "".join(f", {arg}" for arg in split_parameters(args))
                output.extend([f"\n    def {method}(self{parameters}) -> {result}:", "        raise NotImplementedError"])
            else:
                match = MEMBER.fullmatch(line)
                if match is None:
                    raise ValueError(f"Некорректное поле UML: {line}")
                role, annotation = match.groups()
                relation = relations.get((name, role))
                metadata = f"  # uml: {' '.join(relation)}" if relation else ""
                output.append(f"    {role}: {annotation}{metadata}")
    return "\n".join(output) + "\n"


def reverse(source):
    lines = source.splitlines()
    output = [STYLE.rstrip()]
    inheritance = []
    relations = []
    classes = [node for node in ast.parse(source).body if isinstance(node, ast.ClassDef)]
    class_names = {node.name for node in classes}
    for node in classes:
        abstract = (ast.get_docstring(node) or "").startswith("{abstract}")
        kind = "abstract class" if abstract else "class"
        output.append(f"{kind} {node.name} {{")
        for member in node.body:
            if isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                role = member.target.id
                access = "-" if role.startswith("_") else "+"
                output.append(f"  {access} {role}: {ast.unparse(member.annotation)}")
                comment = lines[member.end_lineno - 1].partition("# uml: ")[2]
                if comment:
                    left, arrow, right, target = comment.split()
                    if target not in class_names:
                        raise ValueError(f"Неизвестный класс в связи: {target}")
                    output_relation = f'{node.name} "{left}" {arrow} "{right}" {target} : {role}'
                    if not RELATION.fullmatch(output_relation):
                        raise ValueError(f"Некорректная связь UML: {output_relation}")
                    relations.append(output_relation)
            if isinstance(member, ast.FunctionDef):
                access = "-" if member.name.startswith("_") else "+"
                arguments = ", ".join(
                    f"{arg.arg}: {ast.unparse(arg.annotation)}"
                    for arg in member.args.args if arg.arg != "self"
                )
                output.append(f"  {access} {member.name}({arguments}): {ast.unparse(member.returns)}")
        output.append("}")
        for base in node.bases:
            parent = ast.unparse(base)
            if parent in class_names:
                inheritance.append(f"{parent} <|-- {node.name}")
    return "\n".join([*output, *inheritance, *relations, "@enduml", ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("direction", choices=("forward", "reverse"))
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    transform = forward if args.direction == "forward" else reverse
    args.output.write_text(transform(args.source.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
