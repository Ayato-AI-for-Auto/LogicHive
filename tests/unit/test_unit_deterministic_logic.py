import ast
import pytest
from core.evaluation.plugins.deterministic import DeterministicEvaluator

def test_is_constant_expr_primitives():
    evaluator = DeterministicEvaluator()
    
    # 1. Primitives (Constants)
    assert evaluator._is_constant_expr(ast.parse("1").body[0].value) is True
    assert evaluator._is_constant_expr(ast.parse("'hello'").body[0].value) is True
    assert evaluator._is_constant_expr(ast.parse("True").body[0].value) is True

def test_is_constant_expr_comparisons():
    evaluator = DeterministicEvaluator()
    
    # 2. Trivial Comparisons (Quality Theater)
    assert evaluator._is_constant_expr(ast.parse("1 == 1").body[0].value) is True
    assert evaluator._is_constant_expr(ast.parse("'a' != 'b'").body[0].value) is True
    assert evaluator._is_constant_expr(ast.parse("True is True").body[0].value) is True

def test_is_constant_expr_dynamic():
    evaluator = DeterministicEvaluator()
    
    # 3. Dynamic expressions (Real Testing)
    assert evaluator._is_constant_expr(ast.parse("x == 1").body[0].value) is False
    assert evaluator._is_constant_expr(ast.parse("func() == True").body[0].value) is False
    assert evaluator._is_constant_expr(ast.parse("1 + 1").body[0].value) is False  # binary op not handled as constant yet

def test_is_theatrical_call():
    evaluator = DeterministicEvaluator()
    
    # theatrical: assert_equal(1, 1)
    call_node = ast.parse("assert_equal(1, 1)").body[0].value
    assert evaluator._is_theatrical_call(call_node) is True
    
    # real: assert_equal(x, 1)
    real_call = ast.parse("assert_equal(x, 1)").body[0].value
    assert evaluator._is_theatrical_call(real_call) is False
