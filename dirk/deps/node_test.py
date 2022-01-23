import ast

from dirk.deps.finder import Node
from dirk.test_utils import ASTTestCase


class NodeTestCase(ASTTestCase):
    def test_get_descendant(self):
        const_ast = ast.Constant(value=3)
        classdef_ast = ast.ClassDef(
            "ABC",
            body=[
                ast.Assign(
                    targets=[ast.Name("a", ctx=ast.Store())],
                    value=const_ast,
                )
            ],
        )
        module_ast = ast.Module([classdef_ast])
        node = Node(
            module_ast,
            children={
                "ABC": Node(
                    classdef_ast,
                    children={"a": Node(const_ast)},
                )
            },
        )
        self.assertEqual(
            node.get_descendant("ABC"),
            Node(
                classdef_ast,
                children={"a": Node(const_ast)},
            ),
        )
        self.assertEqual(node.get_descendant("ABC.a"), Node(const_ast))
        self.assertIsNone(node.get_descendant("non_existent"))
        self.assertIsNone(node.get_descendant("ABC.non_existent"))
