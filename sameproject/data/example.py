# An example of an easy way to create data objects that can be validated and
# serialised to/from json, yaml and dictionary objects. Standard Box functions
# like from_json, to_json, from_yaml etc work with validation.

from cerberus import Validator
from box import Box


schema = {
    "example": {"type": "string", "required": True},
}


def _get_validator():
    return Validator(schema)


class Example(Box):
    def __init__(self, *args, frozen_box=True, **kwargs):
        data = Box(*args, **kwargs)
        validator = _get_validator()
        if not validator.validate(data):
            raise Exception(f"Step data is invalid: {validator.errors}")

        super().__init__(*args, frozen_box=frozen_box, **kwargs)
