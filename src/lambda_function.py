"""Implements Lambda function handler.
"""

import logging

import boto3

__version__ = "0.1.0"

log = logging.Logger(__name__)
ec2 = boto3.client("ec2")


def lambda_handler(event, _context):
    """Entry point of the Lambda function."""
    try:
        _lambda_handler(event)
    except:  # pylint: disable=bare-except
        log.exception("ERROR: Uncaught exception")


def _lambda_handler(event):
    if event["action"] == "start":
        state_name = "stopped"
    elif event["action"] == "stop":
        state_name = "running"
    else:
        raise ValueError("Illegal action: {action}".format_map(event))

    paginator = ec2.get_paginator("describe_instances")
    pages = paginator.paginate(
        Filters=[
            {"Name": "tag:Group", "Values": [event["group"]]},
            {"Name": "instance-state-name", "Values": [state_name]},
        ]
    )
    instances = sum(
        [
            sum(
                [[i["InstanceId"] for i in r["Instances"]] for r in p["Reservations"]],
                [],
            )
            for p in pages
        ],
        [],
    )
    if len(instances) == 0:
        return

    if event["action"] == "start":
        ec2.start_instances(InstanceIds=instances)
    elif event["action"] == "stop":
        ec2.stop_instances(InstanceIds=instances)
