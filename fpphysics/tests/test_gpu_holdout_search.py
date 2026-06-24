from fpphysics.gpu_holdout_search import SearchConfig, run_search


def test_gpu_holdout_search_tiny_cpu_run():
    run = run_search(SearchConfig(candidates=64, top_k=2, seed=1, device="cpu", chunk_size=64))
    assert run["candidates"]
    assert run["summary"]["precision_external_stress_pass_candidates"] >= 0
    assert "future sealed tranche" in run["summary"]["strict_warning"]
