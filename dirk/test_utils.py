from unittest import TestCase
import ast


class ASTTestCase(TestCase):
    def assertASTEqual(self, a: ast.AST, b: ast.AST):
        if a is None or b is None:
            self.assertEqual(a, b)
        else:
            self.assertEqual(ast.dump(a, indent=4), ast.dump(b, indent=4))
