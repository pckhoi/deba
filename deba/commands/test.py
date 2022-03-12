import argparse
import sys
import ast
import json

from deba.commands.decorators import subcommand
from deba.config import Config
from deba.deps.expr import ExprPattern
from deba.deps.module import Stack


def exec(conf: Config, args: argparse.Namespace):
    pat = ExprPattern.from_str(args.pattern)
    node = ast.parse(args.function_call).body[0].value
    result = pat.match_node(Stack(), node)
    if result is None:
        print("Does not match")
        sys.exit(1)
    else:
        print("Extracted %s" % json.dumps(result))


@subcommand(exec=exec, open_config=False)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="test", help="test a pattern against a function call"
    )
    parser.add_argument("pattern")
    parser.add_argument("function_call")
    return parser
