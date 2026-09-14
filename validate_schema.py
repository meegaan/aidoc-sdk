import json
import jsonschema

with open(r"c:\Projects\DocAI Core\aidoc-spec\aidoc-1.0.schema.json", "r") as f:
    schema = json.load(f)

for example in ["canonical.json", "semantic.json"]:
    with open(rf"c:\Projects\DocAI Core\aidoc-spec\examples\{example}", "r") as f:
        data = json.load(f)
    print(f"Validating {example}...")
    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f"{example} is VALID.")
    except Exception as e:
        print(f"{example} is INVALID. Error: {e}")
