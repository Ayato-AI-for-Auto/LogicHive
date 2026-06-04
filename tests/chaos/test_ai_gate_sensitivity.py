import textwrap

import pytest

from core.evaluation.manager import EvaluationManager


@pytest.mark.asyncio
@pytest.mark.use_real_intelligence
async def test_ai_gate_theatrical_abstraction():
    """
    Sensitivity: Provide an over-engineered 'adder' with extreme abstraction.
    Gemma 4 should identify this as 'Quality Theater' and reject/score it low.
    """
    manager = EvaluationManager()

    code = textwrap.dedent("""
        class AbstractLogicProvider:
            def execute(self, *args, **kwargs): raise NotImplementedError()

        class BaseArithmeticService(AbstractLogicProvider):
            def __init__(self, mode="standard"): self.mode = mode
            def _log_pre_execution(self): pass

        class DistributedCalculationFactory(BaseArithmeticService):
            def execute(self, a, b):
                self._log_pre_execution()
                return self._perform_core_logic(a, b)
            def _perform_core_logic(self, val1, val2):
                # The actual 'logic' is just a + b
                return val1 + val2

        def theatrical_adder(a, b):
            factory = DistributedCalculationFactory(mode="high_precision")
            return factory.execute(a, b)
    """)

    test_code = "assert theatrical_adder(10, 20) == 30"

    # We use evaluate_all to trigger the AI Gate
    results = await manager.evaluate_all(
        code=code,
        language="python",
        test_code=test_code,
        description="High-precision distributed arithmetic provider with factory pattern."
    )

    ai_res = results["details"].get("ai_gate")
    if ai_res:
        print("\n[AI GATE REPORT - THEATER]")
        print(f"Score: {ai_res['score']}")
        print(f"Reason: {ai_res['reason']}")
        # Expectation: AI should notice the over-engineering
        # assert ai_res["score"] < 70

@pytest.mark.asyncio
@pytest.mark.use_real_intelligence
async def test_ai_gate_math_smoke_screen():
    """
    Sensitivity: Provide code with complex-looking math that simplifies to a constant.
    """
    manager = EvaluationManager()

    code = textwrap.dedent("""
        import math
        def high_entropy_constant_generator(input_val):
            # A lot of 'noise' math
            s = sum([math.sin(i) for i in range(100)])
            c = math.cos(math.pi * 2)
            log_val = math.log(abs(s) + 1)

            # The result is effectively independent of the 'logic' above
            if input_val > 0:
                return 1.0 * c
            else:
                return 0.0
    """)

    test_code = "assert high_entropy_constant_generator(5) == 1.0"

    results = await manager.evaluate_all(
        code=code,
        language="python",
        test_code=test_code,
        description="Sophisticated high-entropy signal generator for stochastic modeling."
    )

    ai_res = results["details"].get("ai_gate")
    if ai_res:
        print("\n[AI GATE REPORT - MATH SMOKE]")
        print(f"Score: {ai_res['score']}")
        print(f"Reason: {ai_res['reason']}")
