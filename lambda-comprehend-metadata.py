# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import sys
import csv
import tarfile
import random
import string

'''
The purpose of this Lambda function is to take .csv files stored in an S3 bucket, decompress them, convert them to a.json file,
and add them to Kendra's central index and then synchronize it. The purpose of this process is for adding metadata to previously stored documents.
'''

comprehend = boto3.client('comprehend')
s3 = boto3.client('s3')
kendra = boto3.client('kendra')

#Random function for Document ID
def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

#Function responsible to read a csv file of the results of the comprehend job
def csv_file(path):
    fields = []
    topics = []
    with open(path, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        # extracting field names through first row
        fields = next(csvreader)

        # extracting each data row one by one
        for row in csvreader:
            topics.append(row)

    topics.append(['1111111','stopper','0.172635'])

    return topics

#Function responsible for extracting the topic with the highest score (the main topic of the document)
def extracting_topics(topics):
    aux_index = topics[0][0]
    aux_score = -1
    aux_topic = ''
    temp = []
    final_topics = []
    for x in topics:
        if x[0] == aux_index:
            if float(x[2]) > aux_score:
                aux_score = float(x[2])
                aux_topic = x[1]
        else:
            temp.extend((aux_index, aux_topic, aux_score))
            final_topics.append(temp)
            temp = []
            aux_index = x[0]
            aux_score = float(x[2])
            aux_topic = x[1]

    return final_topics

#Function responsible to generate the json file to add to our S3 bucket
def generating_json(documents_topics, final_topics, documents_languages):
    count = 0
    for x in documents_topics:
        metadata = {}
        for y in final_topics:
            if x[1] == y[0]:
                title = x[0].split('.')
                metadata = {
                    "DocumentId": get_random_string(10),
                    "Attributes": {
                        "_category": y[1],
                        "_language_code": documents_languages[count]['Languages'][0]['LanguageCode']
                    },
                    "Title": title[0],
                    "ContentType": "PDF"
                }
                with open('/tmp/'+title[0]+'.pdf.metadata.json', 'w') as outfile:
                    json.dump(metadata, outfile)

                with open('/tmp/'+title[0]+'.pdf.metadata.json', 'rb') as data:
                    s3.upload_fileobj(data, 'xxxxxxxxxxxxxxxx', 'metadata/'+title[0]+'.pdf.metadata.json') #Please replace with your bucket name

        count = count +1

def lambda_handler(event, context):
    documents_languages = event['Input']['Payload']['DocumentsLanguages']
    topics_detection_job = comprehend.describe_topics_detection_job(
        JobId=event['Input']['Payload']['TopicDetectionID']
    )
    s3_uri = topics_detection_job['TopicsDetectionJobProperties']['OutputDataConfig']['S3Uri']
    key = s3_uri.split('/')
    key = '/'.join(key[3:7])
    with open('/tmp/topics_file.tar.gz', 'wb') as data:
        s3.download_fileobj('xxxxxxxxxxxxxxxx',key, data) #Please replace with your bucket name

    file = tarfile.open('/tmp/topics_file.tar.gz')
    file.extract('topic-terms.csv', '/tmp/')
    file.extract('doc-topics.csv', '/tmp/')
    file.close()

    topics = csv_file('/tmp/topic-terms.csv')
    documents = csv_file('/tmp/doc-topics.csv')

    final_topics = extracting_topics(topics)
    documents_topics = extracting_topics(documents)

    print(final_topics)
    print(documents_topics)

    generating_json(documents_topics, final_topics, documents_languages)

    kendra.start_data_source_sync_job(
        Id='XXXXXXXXXXXXXXXXXXXX', #Replace with your source ID
        IndexId='XXXXXXXXXXXXXXXXXXXX' #Replace with your index ID
    )
