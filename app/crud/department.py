from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentTree, DepartmentUpdate


def get(db: Session, dept_id: str) -> Department | None:
    return db.query(Department).filter(Department.id == dept_id).first()


def get_all(db: Session) -> list[Department]:
    return db.query(Department).order_by(Department.sort_order, Department.id).all()


def create(db: Session, data: DepartmentCreate) -> Department:
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


def update(db: Session, dept: Department, data: DepartmentUpdate) -> Department:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    db.commit()
    db.refresh(dept)
    return dept


def delete(db: Session, dept: Department) -> None:
    db.delete(dept)
    db.commit()


def build_tree(depts: list[Department]) -> list[DepartmentTree]:
    dept_map: dict[str, DepartmentTree] = {}
    for d in depts:
        dept_map[d.id] = DepartmentTree.model_validate(d)

    roots: list[DepartmentTree] = []
    for dept_out in dept_map.values():
        if dept_out.parent_id is None:
            roots.append(dept_out)
        elif dept_out.parent_id in dept_map:
            dept_map[dept_out.parent_id].children.append(dept_out)

    return roots
