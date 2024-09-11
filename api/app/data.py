import requests
import json

DIFF_TOKEN='0f658147c12a300adb050a896cb213e8'
query='Neo4j'
tag='Natural Language Processing'
size=20
offset=0
search_host = "https://kg.diffbot.com/kg/v3/dql?"
search_query = f'query=type%3AArticle+strict%3Alanguage%3A"en"+sortBy%3Adate'
if query:
    search_query += f'+text%3A"{query}"'
if tag:
    search_query += f'+tags.label%3A"{tag}"'
url = (
    f"{search_host}{search_query}&token={DIFF_TOKEN}&from={offset}&size={size}"
)
# print(url)
data = requests.get(url).json()
with open('data.json', 'w') as json_file:  
    json.dump(data, json_file, indent=4) 