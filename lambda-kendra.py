# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3

kendra = boto3.client('kendra')

'''
The purpose of this Lambda feature is to accelerate the process of integrating Amazon Kendra with our intelligent search solutions.
A simple example of how using the AWS SDK we can consult the information in our central index.
'''

def respond(err, res=None):
    return {
        'statusCode': 200,
        'body': json.dumps(err.message) if err else json.dumps(res)
    }

def lambda_handler(event, context):
    print(event)
    question = event['queryStringParameters']['q']
    print(question)

    #Query using Amazon Kendra
    query_on_kendra = kendra.query(
        IndexId='XXXXXX-XXXXXXX-XXXXXXX', #Replace for your index Id
        QueryText=question,
        PageNumber=1,
        PageSize=5
    )

    results_from_query = query_on_kendra['ResultItems']
    list_of_answers = []
    for x in results_from_query:
        results_score = x['ScoreAttributes']['ScoreConfidence']
        if  results_score == 'HIGH' or results_score == 'VERY_HIGH': #Selecting the most accurate answers
            if x['Type'] == 'ANSWER':
                if x['AdditionalAttributes'][0]['Value']['TextWithHighlightsValue']['Highlights'][0]['TopAnswer']:
                    list_of_answers.append(x['AdditionalAttributes'][0]['Value']['TextWithHighlightsValue']['Text'])
                else:
                    pass
            elif x['Type'] == 'DOCUMENT':
                list_of_answers.append(x['DocumentExcerpt']['Text'])
            else:
                list_of_answers.append(x['AdditionalAttributes'][1]['Value']['TextWithHighlightsValue']['Text'])

    #Generating a Dictionary to store the accurate answers
    answers = {}
    for y in range(len(list_of_answers)):
        key = 'Answer ' + str(y)
        answers[key] = list_of_answers[y]
    return respond(None, answers)
