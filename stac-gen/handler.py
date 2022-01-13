from cmr import GranuleQuery
import json

def handler(event, context):
    """
    Lambda handler for STAC Collection Item generation
    """
    api = GranuleQuery()

    # Granule Id and concept Id refer to the same thing
    # Different terminology is used by different sections of CMR

    concept_id = event['granule_id']
    cmr_json = api.concept_id(concept_id).get_all()

if __name__ == "__main__":
    sample_event = {
        "collection": "OMNO2d",
        "href": "https://acdisc.gesdisc.eosdis.nasa.gov/data//Aura_OMI_Level3/OMNO2d.003/2022/OMI-Aura_L3-OMNO2d_2022m0111_v003-2022m0112t181633.he5",
        "granule_id": "G2199243759-GES_DISC",
    }

    handler(sample_event, {})
