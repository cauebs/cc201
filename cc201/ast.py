from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class CCNameError(Exception):
    pass


class CCTypeError(Exception):
    pass


class CCIndexError(Exception):
    pass


class CCControlFlowError(Exception):
    pass


class Stmt:
    def check(self, ctx: Context):
        print(self)
        raise NotImplementedError


@dataclass
class Block(Stmt):
    stmts: List[Stmt]

    def check(self, ctx: Context):
        inner_ctx = ctx.new_child(self)

        for stmt in self.stmts:
            stmt.check(inner_ctx)


class Expr:
    def check(self, ctx: Context):
        print(self)
        raise NotImplementedError

    def get_type(self, ctx: Context):
        print(self)
        raise NotImplementedError


class PrimType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    NULL = "null"
    BOOLEAN = auto()

    @classmethod
    def from_kw(cls, s):
        return {
            "int": cls.INT,
            "float": cls.FLOAT,
            "string": cls.STRING,
            "null": cls.NULL,
        }[s]


@dataclass
class Type:
    prim: PrimType
    dimensions: int

    def is_number(self):
        numerical_types = [PrimType.INT, PrimType.FLOAT]
        return self.prim in numerical_types and self.dimensions == 0

    def __repr__(self):
        return self.prim.value + self.dimensions * "[]"


@dataclass
class Param:
    ty: Type
    ident: str


@dataclass
class FuncSig:
    params: List[Param]
    return_type: Optional[Type] = None


@dataclass
class FuncDef:
    ident: str
    signature: FuncSig
    body: List[Stmt]

    def check(self, ctx: Context):
        ctx.new_def(self.ident, self.signature)

        inner_ctx = ctx.new_child(self)

        for param in self.signature.params:
            inner_ctx.new_def(param.ident, param.ty)

        for stmt in self.body:
            stmt.check(inner_ctx)


@dataclass
class Return(Stmt):
    value: Optional[Expr]

    def check(self, ctx: Context):
        func = ctx.parent_function()
        expected = func.signature.return_type

        if self.value is None:
            ty = Type(PrimType.NULL, 0)
        else:
            self.value.check(ctx)
            ty = self.value.get_type(ctx)

        if expected is None:
            func.signature.return_type = ty
            return

        if ty != expected:
            raise CCTypeError(
                f"return type mismatch in {func.ident}: "
                f"expected {expected}, got {ty}"
            )


@dataclass
class Program:
    child: Union[Stmt, List[FuncDef]]

    def check(self):
        ctx = Context(self)

        if isinstance(self.child, Stmt):
            self.child.check(ctx)
        else:
            for func_decl in self.child:
                func_decl.check(ctx)


@dataclass
class VarDecl(Stmt):
    ty: PrimType
    ident: str
    dimensions: List[int]

    def check(self, ctx: Context):
        ctx.new_def(self.ident, Type(self.ty, len(self.dimensions)))


@dataclass
class LValue(Expr):
    ident: str
    indices: List[Expr]
    _type: Optional[Type] = None

    def check(self, ctx: Context):
        ty = ctx.get_def(self.ident)

        if isinstance(ty, FuncSig):
            raise CCNameError(
                f"Cannot take value of name '{self.ident}' "
                "which is a function"
            )

        dimensions = ty.dimensions - len(self.indices)

        if dimensions < 0:
            raise CCIndexError(f"Cannot index into type '{ty.prim.value}'")

        for index in self.indices:
            index.check(ctx)

        self._type = Type(ty.prim, dimensions)

    def get_type(self, ctx: Context):
        return self._type


@dataclass
class Attrib(Stmt):
    lvalue: LValue
    value: Expr

    def check(self, ctx: Context):
        self.lvalue.check(ctx)
        self.value.check(ctx)

        ident_type = ctx.get_def(self.lvalue.ident)
        l_dimensions = ident_type.dimensions - len(self.lvalue.indices)
        l_type = Type(ident_type.prim, l_dimensions)

        r_type = self.value.get_type(ctx)

        if r_type != l_type:
            print(self.value)
            raise CCTypeError(
                f"Type mismatch in attribution to '{self.lvalue.ident}': "
                f"expected '{l_type}', got '{r_type}'"
            )

        # TODO: check if indices are in range


@dataclass
class Print(Stmt):
    value: Expr

    def check(self, ctx: Context):
        self.value.check(ctx)


@dataclass
class Read(Stmt):
    lvalue: LValue

    def check(self, ctx: Context):
        self.lvalue.check(ctx)


@dataclass
class If(Stmt):
    condition: Expr
    body: Stmt
    else_body: Optional[Stmt]

    def check(self, ctx: Context):
        self.condition.check(ctx)
        condition_type = self.condition.get_type(ctx)

        if condition_type.dimensions > 0:
            raise CCTypeError(
                "condition must be a comparison operation "
                "or one of: int, float, string, boolean"
            )

        self.body.check(ctx.new_child(self))

        if self.else_body is not None:
            self.else_body.check(ctx.new_child(self))


@dataclass
class For(Stmt):
    init: Attrib
    condition: Expr
    step: Attrib
    body: Stmt

    def check(self, ctx: Context):
        self.init.check(ctx)
        self.condition.check(ctx)
        self.step.check(ctx)

        self.body.check(ctx.new_child(self))


class Break(Stmt):
    def check(self, ctx: Context):
        if not ctx.inside_loop():
            raise CCControlFlowError("'break' can only be used inside a loop.")


@dataclass
class FuncCall(Stmt, Expr):
    ident: str
    args: List[Expr]
    _type: Optional[Type] = None

    def check(self, ctx: Context):
        func_sig = ctx.get_def(self.ident)
        self._type = func_sig.return_type

        for arg, param in zip(self.args, func_sig.params):
            arg.check(ctx)
            arg_type = arg.get_type(ctx)

            if arg_type != param.ty:
                raise CCTypeError(
                    f"Type mismatch in call to '{self.ident}': "
                    f"'{param.ident}' expects {param.ty}, got {arg_type}"
                )

    def get_type(self, ctx: Context):
        return self._type


@dataclass
class Alloc(Expr):
    ty: PrimType
    dimensions: List[Expr]

    def check(self, ctx: Context):
        for dim in self.dimensions:
            dim.check(ctx)

    def get_type(self, ctx: Context):
        return Type(self.ty, len(self.dimensions))


@dataclass
class BinOp(Expr):
    op: str
    lhs: Expr
    rhs: Expr
    _prim_ty: Optional[PrimType] = None

    def check(self, ctx: Context):
        self.lhs.check(ctx)
        self.rhs.check(ctx)

        l_type = self.lhs.get_type(ctx)
        r_type = self.rhs.get_type(ctx)

        if not l_type.is_number() or not r_type.is_number():
            raise CCTypeError(
                f"Invalid operation '{self.op}' on types {l_type} and {r_type}"
            )

        if self.op in ["<=", "<", ">=", ">", "==", "!="]:
            self._prim_ty = PrimType.BOOLEAN
        else:
            self._prim_ty = l_type.prim

    def get_type(self, ctx: Context):
        if self._prim_ty is None:
            raise Exception("unreachable")
        return Type(self._prim_ty, 0)


@dataclass
class UnOp(Expr):
    op: str
    val: Expr
    _type: Optional[Type] = None

    def check(self, ctx: Context):
        ty = self.val.get_type(ctx)

        if not ty.is_number():
            raise CCTypeError(f"Invalid operation '{self.op}' on type '{ty}'")

        self._type = ty

    def get_type(self, ctx: Context):
        return self._type


@dataclass
class Constant(Expr):
    prim_ty: PrimType
    val: Union[int, float, str, None]

    def check(self, ctx: Context):
        pass

    def get_type(self, ctx: Context):
        return Type(self.prim_ty, 0)


@dataclass
class Context:
    node: Any
    symbol_table: Dict[str, Union[Type, FuncSig]] = field(default_factory=dict)
    parent: Optional[Context] = None

    def new_child(self, node):
        return Context(node, parent=self)

    def new_def(self, name, info):
        if name in self.symbol_table:
            raise CCNameError(f"'{name}' is already defined.")

        self.symbol_table[name] = info

    def get_def(self, name):
        ctx = self

        while ctx is not None:
            if name in ctx.symbol_table:
                return ctx.symbol_table[name]

            ctx = ctx.parent

        raise CCNameError(f"Name '{name}' is not defined.")

    def inside_loop(self):
        ctx = self

        while ctx is not None:
            if isinstance(ctx.node, For):
                return True

            ctx = ctx.parent

        return False

    def parent_function(self):
        ctx = self

        while ctx is not None:
            if isinstance(ctx.node, FuncDef):
                return ctx.node

            ctx = ctx.parent

        return None
