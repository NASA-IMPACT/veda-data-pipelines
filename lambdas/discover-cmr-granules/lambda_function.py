from cmr import CollectionQuery, GranuleQuery

api = GranuleQuery(mode="https://cmr.maap-project.org/search/")

def lambda_handler(event, context):
    collection_short_name = event['collection_short_name']
    return api.short_name(collection_short_name).hits()

#print(lambda_handler(event = {'collection_short_name': 'GPM_3IMERGHH'}), {})
