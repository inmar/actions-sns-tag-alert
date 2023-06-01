#!/usr/bin/env python
import json
import os
import re
import subprocess
import sys

import boto3


def get_recent_tags():
    """ Gets the last few tags in the repo; must be using SemVer or similar """

    return (
        subprocess.run(
            "git tag | sort --version-sort -r | head | tr '\n' ' '",
            shell=True,
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .strip()
        .split(" ")
    )


def guess_prev_tag(recent_tags, curr_tag):
    """ Try to guess which tag came before the current one """

    tag_form = re.compile(r"^v?\d+\.\d+\.\d+")
    for tag in recent_tags:
        if tag != curr_tag and tag_form.search(tag):
            return tag

    return "master"


def fix_git_settings():
    """
    The GHA checkout action tries to set up the repo properly, but when you're
    running a follow-up action out of a container the global config isn't
    automatically shared to the container, so you have to reset things manually
    """
    subprocess.run(
        "git config --global --add safe.directory /github/workspace",
        shell=True,
    )


def main():
    fix_git_settings()

    aws_access_key_id, aws_secret_access_key, topic_arn = sys.argv[1:4]
    region = topic_arn.split(":")[3]

    tag_prefix = "refs/tags/"
    git_tag = os.environ["GITHUB_REF"]
    if git_tag.startswith(tag_prefix):
        git_tag = git_tag[len(tag_prefix) :]

    recent_tags = get_recent_tags()
    print(recent_tags)

    prev_tag = "master"
    if recent_tags and len(recent_tags) > 1:
        prev_tag = guess_prev_tag(recent_tags, git_tag)

    data = {
        "tag": git_tag,
        "repo_name": os.environ["GITHUB_REPOSITORY"],
        "prev_tag": prev_tag,
    }

    sns = boto3.client(
        "sns",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region,
    )

    sns.publish(
        TopicArn=topic_arn,
        Subject="[{0}] Tag Created - {1}".format(data["repo_name"], data["tag"]),
        Message=json.dumps(data),
    )


if __name__ == "__main__":
    main()
