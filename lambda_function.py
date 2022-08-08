# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import boto3
import sys
import pdfplumber

'''
The purpose of this Lambda function is to extract text from PDF documents stored in the S3 bucket to convert documents from
PDF to plain text and start a topic detection job using the Amazon Comprehend service.
For the transformation of PDF to plain text, the PDFplumber library is used due to its ease of use and accuracy in extraction.
'''

comprehend = boto3.client('comprehend')
s3 = boto3.client('s3')

#Function responsible for transforming from PDF to plain text
def pdf2text(name_of_the_item):
    with pdfplumber.open(r'/tmp/'+name_of_the_item) as pdf:
        num_pages_per_document = pdf.pages
        all_text = ''
        for pdf_page in num_pages_per_document:
            single_page_text = pdf_page.extract_text()
            all_text = all_text + '\n' + single_page_text

        dominant_language = comprehend.detect_dominant_language(
            Text=pdf.pages[4].extract_text()
        )

    name_of_the_item = name_of_the_item.split('.')
    s3.put_object(
        Body=all_text,
        Bucket='xxxxxxxxxxxxx', #Please replace with your bucket name
        Key='whitepapers-text/'+name_of_the_item[0]+'.txt'
    )

    return dominant_language


def lambda_handler(event, context):

    list_of_objects = s3.list_objects_v2(
        Bucket='axxxxxxxxxxxxxxxxxx', #Please replace with your bucket name
        Prefix='whitepapers'
    )

    list_of_objects['Contents'].pop(0)
    documents_languages = []
    for x in list_of_objects['Contents']:
        exception = x['Key'].split('.')
        if 'pdf' in exception:
            name_of_the_item = x['Key'].split('/')
            with open('/tmp/'+name_of_the_item[1], 'wb') as data:
                s3.download_fileobj('xxxxxxxxxxxxxxxxxxxxxx', x['Key'], data) #Please replace with your bucket name
            dominant_language = pdf2text(name_of_the_item[1])
            documents_languages.append(dominant_language)
        else:
            pass

    topic_detection = comprehend.start_topics_detection_job(
        InputDataConfig={
            'S3Uri': 's3://xxxxxxxxxxxxxxxxxxxxxx/whitepapers-text/', #Replace for your S3 URI
            'InputFormat': 'ONE_DOC_PER_FILE',
        },
        OutputDataConfig={
            'S3Uri': 's3://xxxxxxxxxxxxxxxxxx/whitepapers-text/' #Replace for your S3 URI
        },
        DataAccessRoleArn='arn:aws:iam::xxxxxxxxxx:role/comprehend-role', #Please replace with your role's arn
        JobName='aprendiendoaws-comprehend-topics-detection',
        NumberOfTopics=10
    )

    return {
        'TopicDetectionID': topic_detection['JobId'],
        'DocumentsLanguages': documents_languages
    }
