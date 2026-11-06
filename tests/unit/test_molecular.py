import pytest
from services.ml_molecular.service import molecular_odor_pipeline

def test_valid_smiles_prediction():
    # Vanillin
    vanillin = "O=Cc1cc(OC)c(O)cc1"
    res = molecular_odor_pipeline.predict_odor_descriptors(vanillin)
    assert res["is_valid_smiles"]
    assert res["molecular_weight"] > 100.0
    assert len(res["predicted_descriptors"]) > 0
    # Must contain warning that predictions are statistical, not hazard assays
    assert "statistical perceptual predictions" in res["warning"]

def test_invalid_smiles_rejected():
    invalid_smiles = "NOT_A_VALID_MOLECULE_XYZ%%%"
    res = molecular_odor_pipeline.predict_odor_descriptors(invalid_smiles)
    assert not res["is_valid_smiles"]
    assert "predicted_descriptors" in res
    assert len(res["predicted_descriptors"]) == 0

def test_sulfur_compounds_boost_alliaceous_descriptors():
    # Dimethyl sulfide (garlic/sulfurous)
    dms = "CSC"
    res = molecular_odor_pipeline.predict_odor_descriptors(dms)
    descriptors = [d["descriptor"] for d in res["predicted_descriptors"]]
    assert any(d in descriptors for d in ["sulfurous", "alliaceous", "garlic", "gassy", "meaty"])

def test_isoamyl_acetate_prediction_accuracy():
    # Isoamyl acetate (banana / fruity / sweet)
    isoamyl = "CC(=O)OCCC(C)C"
    res = molecular_odor_pipeline.predict_odor_descriptors(isoamyl)
    assert res["is_valid_smiles"]
    desc_dict = {d["descriptor"]: d["probability"] for d in res["predicted_descriptors"]}
    
    # Must predict fruity/sweet as high confidence
    assert "fruity" in desc_dict or "sweet" in desc_dict
    assert desc_dict.get("fruity", 0.0) > 0.40 or desc_dict.get("sweet", 0.0) > 0.40
    
    # Must NOT suffer from the zero-support single-class bug (roasted/floral=1.0)
    assert desc_dict.get("roasted", 0.0) < 0.50
    assert desc_dict.get("cabbage", 0.0) < 0.50

def test_model_identity_never_claimed_as_openpom():
    info = molecular_odor_pipeline.get_model_info()
    assert "OpenPOM" not in info["model_name"]
    assert "Random Forest" in info["model_name"]
    assert "scaffold" in info["split_method"].lower()
    assert info["macro_roc_auc"] > 0.60
    assert "openpom_comparison" in info
