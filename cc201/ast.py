from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union

from .error import CCBaseError


class CCTypeError(CCBaseError):
    label = "[Type Error]"


class Stmt:
    pass


@dataclass
class Block(Stmt):
    stmts: List[Stmt]


class Expr:
    pass


class Type(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"

    @classmethod
    def from_kw(cls, s):
        return {"int": cls.INT, "float": cls.FLOAT, "string": cls.STRING}[s]


@dataclass
class Param:
    ty: Type
    ident: str
    dimensions: int


@dataclass
class FuncSig:
    param_list: List[Param]
    return_type: Optional[Type] = None


@dataclass
class FuncDef:
    ident: str
    signature: FuncSig
    body: List[Stmt]


@dataclass
class Program:
    children: Union[Stmt, List[FuncDef]]


@dataclass
class VarDecl(Stmt):
    ty: Type
    ident: str
    dimensions: List[int]


@dataclass
class LValue(Expr):
    ident: str
    indices: List[Expr]


@dataclass
class Attrib(Stmt):
    lvalue: LValue
    value: Expr


@dataclass
class Print(Stmt):
    value: Expr


@dataclass
class Read(Stmt):
    lvalue: LValue


@dataclass
class Return(Stmt):
    value: Optional[Expr]


@dataclass
class If(Stmt):
    condition: Expr
    body: Stmt
    else_body: Optional[Stmt]


@dataclass
class For(Stmt):
    init: Attrib
    condition: Expr
    step: Attrib
    body: Stmt


class Break(Stmt):
    pass


@dataclass
class FuncCall(Stmt, Expr):
    ident: str
    args: List[Expr]


@dataclass
class Alloc(Expr):
    ty: Type
    dimensions: List[Expr]


@dataclass
class BinOp(Expr):
    op: str
    lhs: Expr
    rhs: Expr


@dataclass
class UnOp(Expr):
    op: str
    val: Expr


@dataclass
class Constant(Expr):
    val: Union[int, float, str, None]
