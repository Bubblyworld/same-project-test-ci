import sys
import click
import glob
from pathlib import Path
from kfp.compiler import Compiler
from kfp.v2 import compiler
import importlib
import os
import kfp
from kfp.v2 import dsl
from kfp.v2.dsl import component, Output, HTML
from . import deploy
import render


@click.group()
def main():
    """
    Debug your SAME project compiled vertex pipelines.
    """


@click.command(
    context_settings=dict(
        ignore_unknown_options=False,
        allow_extra_args=False,
    )
)
@click.option(
    "--compiled-directory",
    "compiled_directory",
    help="Directory in which your file exists",
    show_default=True,
    required=True,
)
def compile_kfp(compiled_directory: str):
    """
    Compile the rendered files into a .yaml for direct deployment to Kubeflow.
    """
    sys.path.append(compiled_directory)
    p = Path(compiled_directory)
    root_files = [f for f in p.glob("root_pipeline_*.py")]
    if len(root_files) < 1:
        raise ValueError(f"No root files found in {compiled_directory}")
    elif len(root_files) > 1:
        raise ValueError(f"More than one root file found in {compiled_directory}: {', '.join(root_files)}")
    else:
        root_file = root_files.pop()

    print(f"Root file: {root_file}")
    mod = root_file.stem

    root_module = importlib.import_module(mod)

    package_yaml_path = p / f"{root_file.stem}.yaml"

    print(f"Package path: {package_yaml_path}")

    Compiler(mode=kfp.dsl.PipelineExecutionMode.V1_LEGACY).compile(pipeline_func=root_module.root, package_path=str(package_yaml_path))


@click.command(
    context_settings=dict(
        ignore_unknown_options=False,
        allow_extra_args=False,
    )
)
@click.option(
    "--compiled-pipeline-path",
    "compiled_pipeline_path",
    help="The path to your compiled pipeline YAML file. It can be a local path or a Google Cloud Storage URI.",
    show_default=True,
    required=True,
)
@click.option(
    "--root-module-name",
    "root_module_name",
    help="Root module name.",
    show_default=True,
    required=True,
)
def deploy_kfp(compiled_pipeline_path: Path, root_module_name: str):
    """
    Deploy the .yaml to Kubeflow
    """
    return deploy(compiled_path=compiled_pipeline_path, root_module_name=root_module_name)


main.add_command(compile_kfp)
main.add_command(deploy_kfp)

# https://click.palletsprojects.com/en/8.1.x/options/#values-from-environment-variables
if __name__ == "__main__":
    main(auto_envvar_prefix="SAME")

# Steps:
# Tested on GCP
# export PIPELINE_VERSION=1.8.1
# kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
# kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
# kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"

# export PIPELINE_VERSION=1.8.1
# kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
# kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
# kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"
