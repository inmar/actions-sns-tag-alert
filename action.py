#!/usr/bin/env python
import json
import os
import re
import subprocess
import sys

from argparse import (ArgumentParser, ArgumentTypeError, RawTextHelpFormatter)

import boto3


def arg_parser():
    """ Set up CLI argument parsing """
    parser = ArgumentParser(
        description="Creates a 'new tag' alert",
        formatter_class=RawTextHelpFormatter,
        epilog="\n\n",
    )

    parser.add_argument(
        "-i",
        "--aws-id",
        dest="aws_access_key_id",
        type=str,
        required=True,
        help="AWS Key ID",
    )

    parser.add_argument(
        "-k",
        "--aws-key",
        dest="aws_secret_access_key",
        type=str,
        required=True,
        help="AWS Secret Access Key",
    )

    parser.add_argument(
        "-t",
        "--topic-arn",
        dest="topic_arn",
        type=sns_arn_type,
        required=True,
        help="SNS Topic ARN",
    )

    parser.add_argument(
        "-p",
        "--tag-pattern",
        dest="tag_pattern",
        type=str,
        default=r"^v?\d+\.\d+\.\d+",
        help="Regex pattern for valid tags",
    )

    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually send the notification",
    )

    args = parser.parse_args()

    return args


def sns_arn_type(val):
    if not re.match(r"arn:aws:sns:[a-z0-9-]+:\d{12}:[a-zA-Z0-9-_]+(.fifo)?", val):
        raise ArgumentTypeError("Invalid ARN format: {0}".format(val))

    return val


def get_recent_tags(tag_pattern):
    """ Gets the last few tags in the repo; must be using SemVer or similar """

    return (
        subprocess.run(
            "git tag --sort=-v:refname | grep -P '{0}' | head | tr '\n' ' '".format(tag_pattern),
            shell=True,
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .strip()
        .split(" ")
    )


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


def main(args):
    fix_git_settings()

    tag_prefix = "refs/tags/"
    git_tag = os.environ["GITHUB_REF"]
    if git_tag.startswith(tag_prefix):
        git_tag = git_tag[len(tag_prefix) :]

    recent_tags = get_recent_tags(args.tag_pattern)
    print(recent_tags)

    prev_tag = "master"
    if recent_tags and len(recent_tags) > 1:
        prev_tag = next((tag for tag in recent_tags if tag != git_tag), "master")

    data = {
        "tag": git_tag,
        "repo_name": os.environ["GITHUB_REPOSITORY"],
        "prev_tag": prev_tag,
    }

    if args.commit:
        sns = boto3.client(
            "sns",
            aws_access_key_id=args.aws_access_key_id,
            aws_secret_access_key=args.aws_secret_access_key,
            region_name=args.topic_arn.split(":")[3],
        )

        sns.publish(
            TopicArn=args.topic_arn,
            Subject="[{0}] Tag Created - {1}".format(data["repo_name"], data["tag"]),
            Message=json.dumps(data),
        )
    else:
        print(json.dumps(data, indent=4, sort_keys=True, default=str))


if __name__ == "__main__":
    main(arg_parser())
