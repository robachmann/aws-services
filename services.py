import json


class Service:
    id: str
    name: str
    product_name: str
    category: str
    launch_date: str
    summary: str
    url: str
    regions: [str]

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
