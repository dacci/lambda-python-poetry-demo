from unittest.mock import MagicMock

import boto3_mocking
import pytest


@pytest.fixture(scope="package", autouse=True)
def boto3_patching():
    with boto3_mocking.patching:
        yield


@pytest.fixture(scope="package")
def ec2():
    mock = MagicMock()

    with boto3_mocking.clients.handler_for("ec2", lambda: mock):
        yield mock


def test_start(ec2, mocker):
    paginator = mocker.MagicMock()
    get_paginator = mocker.patch.object(ec2, "get_paginator", return_value=paginator)
    describe_instances = mocker.patch.object(
        paginator,
        "paginate",
        return_value=[
            {
                "Reservations": [
                    {"Instances": [{"InstanceId": "i-001"}, {"InstanceId": "i-002"}]}
                ]
            },
            {"Reservations": [{"Instances": [{"InstanceId": "i-003"}]}]},
        ],
    )
    start_instances = mocker.patch.object(ec2, "start_instances")
    stop_instances = mocker.patch.object(ec2, "stop_instances")

    from lambda_function import lambda_handler

    lambda_handler({"action": "start", "group": "hoge"}, None)

    get_paginator.assert_called_once_with("describe_instances")
    describe_instances.assert_called_once_with(
        Filters=[
            {"Name": "tag:Group", "Values": ["hoge"]},
            {"Name": "instance-state-name", "Values": ["stopped"]},
        ]
    )
    start_instances.assert_called_once_with(InstanceIds=["i-001", "i-002", "i-003"])
    stop_instances.assert_not_called()


def test_stop(ec2, mocker):
    paginator = mocker.MagicMock()
    get_paginator = mocker.patch.object(ec2, "get_paginator", return_value=paginator)
    describe_instances = mocker.patch.object(
        paginator,
        "paginate",
        return_value=[
            {"Reservations": [{"Instances": [{"InstanceId": "i-001"}]}]},
            {
                "Reservations": [
                    {"Instances": [{"InstanceId": "i-002"}, {"InstanceId": "i-003"}]}
                ]
            },
        ],
    )
    start_instances = mocker.patch.object(ec2, "start_instances")
    stop_instances = mocker.patch.object(ec2, "stop_instances")

    from lambda_function import lambda_handler

    lambda_handler({"action": "stop", "group": "piyo"}, None)

    get_paginator.assert_called_once_with("describe_instances")
    describe_instances.assert_called_once_with(
        Filters=[
            {"Name": "tag:Group", "Values": ["piyo"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )
    start_instances.assert_not_called()
    stop_instances.assert_called_once_with(InstanceIds=["i-001", "i-002", "i-003"])


def test_start_no_match(ec2, mocker):
    paginator = mocker.MagicMock()
    get_paginator = mocker.patch.object(ec2, "get_paginator", return_value=paginator)
    describe_instances = mocker.patch.object(
        paginator, "paginate", return_value=[{"Reservations": []}]
    )
    start_instances = mocker.patch.object(ec2, "start_instances")
    stop_instances = mocker.patch.object(ec2, "stop_instances")

    from lambda_function import lambda_handler

    lambda_handler({"action": "start", "group": "fuga"}, None)

    get_paginator.assert_called_once_with("describe_instances")
    describe_instances.assert_called_once_with(
        Filters=[
            {"Name": "tag:Group", "Values": ["fuga"]},
            {"Name": "instance-state-name", "Values": ["stopped"]},
        ]
    )
    start_instances.assert_not_called()
    stop_instances.assert_not_called()


def test_unknown_action(ec2, mocker):
    describe_instances = mocker.patch.object(ec2, "describe_instances")

    from lambda_function import lambda_handler

    lambda_handler({"action": "test", "group": "fuga"}, None)

    describe_instances.assert_not_called()
