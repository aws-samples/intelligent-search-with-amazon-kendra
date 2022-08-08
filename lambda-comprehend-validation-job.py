# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3

'''
The purpose of this Lambda function is to validate whether the topic detection job in Amazon Comprehend has finished or is still in progress.
'''

comprehend = boto3.client('comprehend')

def lambda_handler(event, context):
    print(event)
    status_of_topics_job = comprehend.describe_topics_detection_job(
        JobId=event['Input']['Payload']['TopicDetectionID']
    )

    return {
        'TopicDetectionID': status_of_topics_job['TopicsDetectionJobProperties']['JobId'],
        'DetectionJobStatus': status_of_topics_job['TopicsDetectionJobProperties']['JobStatus'],
        'DocumentsLanguages': event['Input']['Payload']['DocumentsLanguages']
    }
