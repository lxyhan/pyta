import astroid
import pylint.testutils
from astroid import nodes

from python_ta.cfg import CFGVisitor
from python_ta.checkers.condition_logic_checker import ConditionLogicChecker
from python_ta.transforms.z3_visitor import Z3Visitor


class TestImpossibleConditionChecker(pylint.testutils.CheckerTestCase):
    CHECKER_CLASS = ConditionLogicChecker
    CONFIG = {"z3": True}

    def test_impossible_by_precondition(self):
        src = """
        def func(x: float):
            '''
            Preconditions:
                - x > 5.0
            '''
            if x < 0.0:
                print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_impossible_by_if_condition(self):
        src = """
        def func(x: int):
            if x > 5:
                if x < 3:
                    print(x)
        """
        *_, condition_node = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_impossible_conditional_statement(self):
        src = """
        def func(x: int):
            if x > 0 and x < 0:
                print("impossible")
        """
        *_, condition_node = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_impossible_if_else(self):
        src = """
        def func(x: int):
            '''
            Preconditions:
                - x > 0
            '''
            if x <= 0:
                return x
            else:
                return 0
        """
        *_, condition_node = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_impossible_by_while_condition(self):
        src = """
        def func(x: int):
            '''
            Preconditions:
                - x > 10
            '''
            while x > 0:
                if x < 0:
                    print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_impossible_condition_multiple_if_else(self):
        src = """
        def func(x: int):
            '''
            Preconditions:
                - x in {1, 2, 3}
            '''
            if x == 1:
                print(1)
            elif x == 2:
                print(2)
            elif x == 4:
                print(2)
            elif x == 3:
                print(3)
            else:
                print(0)
        """
        _, _, condition_node, _ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_impossible_condition_repeat_checking_if_else(self):
        src = """
        def func(x: int):
            '''
            Preconditions:
                - x in {1, 2, 3}
            '''
            if x == 1:
                print(1)
            elif x == 2:
                print(2)
            elif x == 2:
                print(2)
            elif x == 3:
                print(3)
            else:
                print(0)
        """
        _, _, condition_node, _ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertAddsMessages(
            pylint.testutils.MessageTest(msg_id="impossible-condition", node=condition_node.test),
            ignore_position=True,
        ):
            self.checker.visit_if(condition_node)

    def test_possible_condition(self):
        src = """
        def func(x: str):
            '''
            Preconditions:
                - x[0:2] == "ab"
            '''
            if x == "abc":
                print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def test_partially_impossible_condition(self):
        src = """
        def func(x: int):
            '''
            Preconditions:
                - x > 5
            '''
            if x > 10 or x < 5:
                print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def test_impossible_condition_variable_reassignment(self):
        src = """
        def func(x: int, y: bool):
            '''
            Preconditions:
                - x > 10
            '''
            if not y:
                x = -1
            if x < 0:
                print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def test_impossible_condition_partial_path(self):
        src = """
        def func(x: int):
            if x > 5:
                print(x)
            else:
                print(x)
            if x < 0:
                print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def test_not_impossible_by_reassignment(self):
        src = """
        def func(x: float):
            '''
            Preconditions:
                - x in [1.0, 2.0]
            '''
            x = None
            if x == 3.0:
                print(x)
        """
        condition_node, *_ = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def test_not_impossible_by_reassignment_one_path(self):
        src = """
        def func(x: str, y: int):
            '''
            Preconditions:
                - x in {"a", "b"}
            '''
            if y > 0:
                x = "c"
            if x == "c":
                print(x)
        """
        *_, condition_node = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def test_unparsed_condition(self):
        src = """
        def func(a: int):
            if a > 5:
                print(a)
        """

        *_, condition_node = self._apply_cfg_visitor(src).nodes_of_class(nodes.If)

        with self.assertNoMessages():
            self.checker.visit_if(condition_node)

    def _apply_cfg_visitor(self, src: str) -> nodes.NodeNG:
        z3v = Z3Visitor()
        mod = z3v.visitor.visit(astroid.parse(src))
        mod.accept(CFGVisitor(options={"separate-condition-blocks": True}, z3_enabled=True))
        return mod
