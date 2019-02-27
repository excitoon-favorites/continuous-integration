#!/usr/bin/env python3
#
# Copyright 2018 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import yaml

import bazelci
from bazelci import BuildkiteException

BUILD_STATUS_API_URL = "https://api.buildkite.com/v2/organizations/bazel/pipelines/bazelisk-plus-incompatible-flags/builds/"

ENCRYPTED_BUILDKITE_API_TOKEN = """
CiQA4DEB9ldzC+E39KomywtqXfaQ86hhulgeDsicds2BuvbCYzsSUAAqwcvXZPh9IMWlwWh94J2F
exosKKaWB0tSRJiPKnv2NPDfEqGul0ZwVjtWeASpugwxxKeLhFhPMcgHMPfndH6j2GEIY6nkKRbP
uwoRMCwe
""".strip()


def buildkite_token():
    return (
        subprocess.check_output(
            [
                bazelci.gcloud_command(),
                "kms",
                "decrypt",
                "--project",
                "bazel-untrusted",
                "--location",
                "global",
                "--keyring",
                "buildkite",
                "--key",
                "buildkite-untrusted-api-token",
                "--ciphertext-file",
                "-",
                "--plaintext-file",
                "-",
            ],
            input=base64.b64decode(ENCRYPTED_BUILDKITE_API_TOKEN),
            env=os.environ,
        )
        .decode("utf-8")
        .strip()
    )


def get_build_status_api_url(build_number):
    return BUILD_STATUS_API_URL + "%s?access_token=%s" % (build_number, buildkite_token())


def get_build_info(build_number):
    output = subprocess.check_output(["curl", get_build_status_api_url(build_number)]).decode(
        "utf-8"
    )
    build_info = json.loads(output)
    return build_info

def print_result_info_jobs(build_number):
    info_text = ["Hello buildkite"]
    pipeline_steps = []
    pipeline_steps.append(bazelci.create_step(
        label="Hello buildkite",
        commands=[
            'buildkite-agent annotate --context="Say hello" --style=info "\n' + "\n".join(info_text) + '\n"'
        ],
    ))
    pipeline_steps.append(bazelci.create_step(
        label="Success",
        commands=[
            'buildkite-agent annotate --context="Say success" --style=success "\n' + "\n".join(info_text) + '\n"'
        ],
    ))
    pipeline_steps.append(bazelci.create_step(
        label="Failure",
        commands=[
            'buildkite-agent annotate --context="Say error" --style=error "\n' + "\n".join(info_text) + '\n"'
        ],
    ))
    print(yaml.dump({"steps": pipeline_steps}))

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Script to aggregate `bazelisk --migrate` test result for incompatible flags and generate pretty Buildkite info messages."
    )
    parser.add_argument("--build_number", type=str)

    args = parser.parse_args(argv)
    try:
        if args.build_number:
            print_result_info_jobs(args.build_number)
        else:
            parser.print_help()
            return 2

    except BuildkiteException as e:
        bazelci.eprint(str(e))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
