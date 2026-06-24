from fpphysics.engine import DerivationEngine


def test_default_models_run_and_score():
    engine = DerivationEngine()
    results = engine.evaluate_default_models()
    assert len(results) >= 4
    names = [r.model_name for r in results]
    assert any("non-SUSY" in n for n in names)
    assert any(r.dof_predictive > 0 for r in results)


def test_cosmological_constant_hierarchy_is_huge():
    engine = DerivationEngine()
    target = engine.targets["Lambda_lP^2"]
    assert 1e-123 < target.value < 1e-121
