MEDICAL_FACTS_SCHEMA_V1 = {
    "conditions": {
        "diabetes_type": "type1 | type2 | none | unknown",
        "asthma": False,
        "arthritis": False,
        "active_cancer": False
    },
    "diabetes_control": {
        "a1c": None,
        "a1c_date": None,
        "insulin_pump_or_cgm": False,
        "recurrent_hypoglycemia": False,
        "dka_hospitalization": False
    },
    "microvascular": {
        "neuropathy": False,
        "retinopathy_stage": "none | non_proliferative | proliferative | unknown",
        "ckd_stage": None
    },
    "macrovascular": {
        "tia": False,
        "stroke": False,
        "cad_mi": False,
        "pvd": False
    },
    "medications": {
        "dual_antiplatelet": False,
        "midodrine": False,
        "chronic_med_count": None,
        "has_glucagon": False
    },
    "stability": {
        "last_hospitalization_months_ago": None,
        "last_dka_years_ago": None,
        "labs_worsening": False
    }
}
