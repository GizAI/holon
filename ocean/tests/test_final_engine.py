import importlib.util
from pathlib import Path
import sys

spec=importlib.util.spec_from_file_location('eng', str(Path(__file__).resolve().parents[1]/'src'/'bhf_ocean_final_engine.py'))
eng=importlib.util.module_from_spec(spec)
sys.modules['eng']=eng
spec.loader.exec_module(eng)

def test_threshold_certificate_unique():
    cert=eng.threshold_certificate()
    assert cert['number_of_nonnegative_integer_solutions']==1792
    assert cert['minimal_dimension']==62
    assert cert['number_of_minimizers']==1
    assert cert['unique_minimizer']==(1,1,1,1,1,1,2,2,1)

def test_bhf_gauge_values():
    r=eng.bhf_bc4().compute()
    assert abs(r['alpha_em_inv_MZ']-127.956742827056)<1e-9
    assert abs(r['sin2_MSbar_MZ']-0.231188712312)<1e-12
    assert abs(r['alpha_s_MZ']-0.118205763021)<1e-12

def test_d5_reference_values():
    r=eng.d5_reference().compute()
    assert abs(r['alpha_em_inv_MZ']-127.928418368491)<1e-9
    assert abs(r['alpha_s_MZ']-0.118000699956)<1e-12
