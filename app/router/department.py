from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import department as crud
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentTree, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    return crud.get_all(db)


@router.get("/tree", response_model=list[DepartmentTree])
def get_department_tree(db: Session = Depends(get_db)):
    depts = crud.get_all(db)
    return crud.build_tree(depts)


@router.get("/{dept_id}", response_model=DepartmentOut)
def get_department(dept_id: str, db: Session = Depends(get_db)):
    dept = crud.get(db, dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    return dept


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    if data.parent_id and not crud.get(db, data.parent_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父部门不存在")
    return crud.create(db, data)


@router.put("/{dept_id}", response_model=DepartmentOut)
def update_department(dept_id: str, data: DepartmentUpdate, db: Session = Depends(get_db)):
    dept = crud.get(db, dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    if data.parent_id and not crud.get(db, data.parent_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父部门不存在")
    return crud.update(db, dept, data)


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(dept_id: str, db: Session = Depends(get_db)):
    dept = crud.get(db, dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")
    if dept.children:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先删除子部门")
    if dept.users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="部门下存在用户，无法删除")
    crud.delete(db, dept)
