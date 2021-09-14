from cli.same.same_config import schema, SAMEValidator
from cerberus import SchemaError
from cli.same import helpers
import pytest
from pathlib import Path
from ruamel.yaml import YAML

same_config_file_path = "test/testdata/sample_same_configs/good_same.yaml"

# Test name, Same File Path, Valid, Num of Errors, Field, Error Type or Error Phrase
sample_same_file_paths = [
    ("Good SAME Config", "test/testdata/sample_same_configs/good_same.yaml", True, 0, "", ""),
    ("No API Version", "test/testdata/sample_same_configs/no_apiVersion.yaml", False, 1, "apiVersion", "required"),
    ("No Default Base Image", "test/testdata/sample_same_configs/no_default_for_base_images.yaml", False, 1, "base_images", "'default' entry"),
]


def test_load_same_config():
    # just testing that we can test the compile verb

    same_file_path = Path(same_config_file_path)
    assert same_file_path.exists()

    with open(same_config_file_path, "rb") as f:
        same_config_file_contents = helpers.load_same_config_file(f)

    assert same_config_file_contents != ""


def test_must_have_default():

    with open(same_config_file_path, "rb") as f:
        good_same_config_file_contents = helpers.load_same_config_file(f)

    has_default_yaml = """
base_images:
    default:
        image_tag: library/python:3.9-slim-buster
    private_environment:
        image_tag: sameprivateregistry.azurecr.io/sample-private-org/sample-private-image:latest
        private_registry: true
"""

    no_default_yaml = """
base_images:
    private_environment:
        image_tag: sameprivateregistry.azurecr.io/sample-private-org/sample-private-image:latest
        private_registry: true
"""
    yaml = YAML(typ="safe")
    has_default = yaml.load(has_default_yaml)
    no_default = yaml.load(no_default_yaml)

    has_default_full = good_same_config_file_contents | has_default
    no_default_full = good_same_config_file_contents | no_default

    v = SAMEValidator(schema)
    v.validate(has_default_full)
    assert len(v._errors) == 0
    v.validate(no_default_full)
    assert len(v._errors) == 1


def test_same_config_schema_compiles():
    try:
        v = SAMEValidator(schema)
    except SchemaError as e:
        pytest.fail(f"Schema failed to validate: {e}")

    assert v is not None


@pytest.mark.parametrize("test_name, same_config_file_path, valid, num_errors, error_field, error_type", sample_same_file_paths, ids=[p[0] for p in sample_same_file_paths])
def test_load_sample_same_configs(caplog, test_name, same_config_file_path, valid, num_errors, error_field, error_type):
    v = SAMEValidator(schema)
    with open(same_config_file_path, "rb") as f:
        same_config_file_contents = helpers.load_same_config_file(f)
    validated = v.validate(same_config_file_contents)

    assert validated is valid, print(f"Unable to validate same config: {v.errors}")
    assert num_errors == len(v._errors)
    if num_errors > 0:
        error = v.document_error_tree[error_field].errors[0]
        if error.rule:
            assert error.rule == error_type
        else:
            assert error_type in error.info[0]


def test_e2e_load_same_object(caplog):
    with open(same_config_file_path, "rb") as f:
        same_config_object = helpers.load_same_config_file(f)

    assert same_config_object.notebook.path == "sample_notebook.ipynb"
    assert same_config_object.metadata.name == "SampleComplicatedNotebook"
    assert len(same_config_object.base_images.default.packages) == 2
    assert len(same_config_object.datasets.USER_HISTORY.environments) == 3
    assert isinstance(same_config_object.run.parameters, dict)
