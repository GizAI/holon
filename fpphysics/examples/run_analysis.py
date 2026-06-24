import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fpphysics.engine import DerivationEngine

engine = DerivationEngine()
for result in engine.evaluate_default_models():
    print(result.model_name)
    print("  verdict:", result.verdict)
    print("  predictive chi2/dof:", result.chi2_predictive, result.dof_predictive)
    for name, score in result.scores.items():
        role = "prediction" if score.counted_as_prediction else "fit/control"
        print(f"  {name}: pred={score.prediction.value:.12g}, target={score.target.value:.12g}, z={score.z}, {role}")
