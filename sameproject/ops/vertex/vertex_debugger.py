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
from google.cloud import aiplatform


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
def compile_vertex(compiled_directory: str):
    sys.path.append(compiled_directory)
    p = Path(compiled_directory)
    root_files = [f for f in p.glob("root_pipeline_*")]
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

    Compiler(mode=kfp.dsl.PipelineExecutionMode.V2_COMPATIBLE).compile(pipeline_func=root_module.root, package_path=str(package_yaml_path))


@click.command(
    context_settings=dict(
        ignore_unknown_options=False,
        allow_extra_args=False,
    )
)
@click.option(
    "--compiled-pipeline-path",
    "compiled_pipeline_path",
    help="The path to your compiled pipeline JSON file. It can be a local path or a Google Cloud Storage URI.",
    show_default=True,
    required=True,
)
@click.option(
    "--project-id",
    "project_id",
    help="The project that you want to run the pipeline in.",
    show_default=True,
    required=True,
)
@click.option(
    "--pipeline-root",
    "pipeline_root",
    help="The pipeline-root parameter specifies where the output of the pipeline should be stored. This pipeline saves run artifacts to the AI Platform Pipelines default Cloud Storage bucket.",
    show_default=True,
    required=True,
)
@click.option(
    "--service-account",
    "service_account",
    help="Service principal to run this pipeline under.",
    show_default=True,
    required=True,
)
@click.option(
    "--service-account-credentials-file",
    "service_account_credentials_file",
    help="JSON file containing credentials for the service account.",
    show_default=True,
    required=True,
)
def deploy_vertex(compiled_pipeline_path: str, project_id: str, pipeline_root: str, service_account: str, service_account_credentials_file: str):
    from google.cloud import aiplatform

    job = aiplatform.PipelineJob(
        display_name="MY_DISPLAY_JOB",
        template_path=compiled_pipeline_path,
        project=project_id,
        pipeline_root=pipeline_root,
        credentials=service_account_credentials_file,
    )

    # job = aiplatform.PipelineJob(
    #     display_name="MY_DISPLAY_JOB",
    #     template_path=compiled_pipeline_path,
    #     job_id=JOB_ID,
    #     pipeline_root=PIPELINE_ROOT_PATH,
    #     parameter_values=PIPELINE_PARAMETERS,
    #     enable_caching=ENABLE_CACHING,
    #     encryption_spec_key_name=CMEK,
    #     labels=LABELS,
    #     credentials=CREDENTIALS,
    #     project=PROJECT_ID,
    #     location=LOCATION,
    # )

    job.submit(service_account=service_account)
    # job.submit(service_account=SERVICE_ACCOUNT, network=NETWORK)


main.add_command(compile_vertex)
main.add_command(deploy_vertex)

# https://click.palletsprojects.com/en/8.1.x/options/#values-from-environment-variables
if __name__ == "__main__":
    main(auto_envvar_prefix="SAME")

# Steps:

# - Create Service Principal to run - https://cloud.google.com/vertex-ai/docs/pipelines/configure-project#service-account
# -
#   - gcloud iam service-accounts create vertex-runner-sp \
# --description="Service principal for running vertex and creating pipelines/metadata" \
# --display-name="VERTEX_RUNNER_SP" \
# --project=scorpio-216915

# gcloud projects add-iam-policy-binding $PROJECT_ID \
#     --member="serviceAccount:$SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com" \
#     --role="roles/aiplatform.user"

# gcloud iam service-accounts add-iam-policy-binding \
#     $SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com \
#     --member="user:$USER_EMAIL" \
#     --role="roles/iam.serviceAccountUser"
# - Create a cloud bucket
# gsutil mb -p PROJECT_ID -l BUCKET_LOCATION gs://BUCKET_NAME
# - Enable APIs -

# export PROJECT_ID="scorpio-216915"
# export SERVICE_ACCOUNT_ID="vertex-runner-sp"
# export USER_EMAIL="aronchick@busted.dev"
# export BUCKET_NAME="same_test_bucket"
# export FILE_NAME="vertex_sp_credentials"

#     gcloud projects add-iam-policy-binding $PROJECT_ID \
#         --member="serviceAccount:$SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com" \
#         --role="roles/aiplatform.user"

#     gcloud iam service-accounts add-iam-policy-binding \
#         $SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com \
#         --member="user:$USER_EMAIL" \
#         --role="roles/iam.serviceAccountUser"

#     gsutil iam ch \
#     serviceAccount:$SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectCreator,objectViewer \
#     gs://$BUCKET_NAME

# Download the service account credentials
# https://cloud.google.com/docs/authentication/getting-started#auth-cloud-implicit-python
# gcloud iam service-accounts keys create $FILE_NAME.json --iam-account=$SERVICE_ACCOUNT_ID@$PROJECT_ID.iam.gserviceaccount.com
