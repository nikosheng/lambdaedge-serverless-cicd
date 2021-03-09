# Lambda@Edge CICD Pipeline

## Prerequiste

### CloudFront Distribution
You should have already setup a CloudFront distribution for Lambda@Edge function to be associated with. For more information about how to create CloudFront distribution, please refer to [Getting started with Amazon CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.html)

### Serverless Framework
The Serverless Framework helps you develop and deploy your AWS Lambda functions, along with the AWS infrastructure resources they require. It's a CLI that offers structure, automation and best practices out-of-the-box, allowing you to focus on building sophisticated, event-driven, serverless architectures, comprised of Functions and Events. For more information about Serverless Framework on AWS, please refer to 
[Serverless Framework on AWS](https://www.serverless.com/framework/docs/providers/aws/guide/intro/)

## Procedure
After we prepare above steps, we could start the journey of building up Lambda@Edge pipeline to accelerate the development cycle.

First of all, we need to create a serverless new project with serverless framework

```
$ sls create -t aws-python3 --path lambdaedge-cicd-project
```

Then we could enter the folder `lambdaedge-cicd-project` we created before and we would see 2 files `handler.py` and `serverless.yml` are already existed. `serverless.yml` is the key file to deploy our project to AWS. As for our pipeline, we could clone this repo and copy the `serverless.yml` to our project.

```
service: lambdaedge-cicd-project

frameworkVersion: '2'

provider:
  name: aws
  runtime: python3.8
  lambdaHashingVersion: 20201221
  region: us-east-1

# you can add statements to the Lambda function's IAM Role here
  role: 
    Fn::GetAtt:
        - lambdaEdgeRole
        - Arn

package:
  exclude:
    - node_modules/**
    - package-lock.json

functions:
  # viewerRequest:
  #   handler: lambdaEdge/handler
  #   events:
  #     - preExistingCloudFront:
  #       # ---- Mandatory Properties -----
  #         distributionId: E3BKY5OQ26MZ4W # CloudFront distribution ID you want to associate
  #         eventType: origin-response # Choose event to trigger your Lambda function, which are `viewer-request`, `origin-request`, `origin-response` or `viewer-response`
  #         pathPattern: '*.png' # Specifying the CloudFront behavior
  #         includeBody: false # Whether including body or not within request
  #       # ---- Optional Property -----
  #         #stage: dev # Specify the stage at which you want this CloudFront distribution to be updated
  originResponse:
    handler: lambdaEdge/originResponse.handler
    events:
      - preExistingCloudFront:
        # ---- Mandatory Properties -----
          distributionId: E3BKY5OQ26MZ4W # CloudFront distribution ID you want to associate
          eventType: origin-response # Choose event to trigger your Lambda function, which are `viewer-request`, `origin-request`, `origin-response` or `viewer-response`
          pathPattern: '*.png' # Specifying the CloudFront behavior
          includeBody: false # Whether including body or not within request
        # ---- Optional Property -----
          #stage: dev # Specify the stage at which you want this CloudFront distribution to be updated

resources:
  Resources:
    lambdaEdgeRole:
      Type: AWS::IAM::Role
      Properties:
        Path: /
        RoleName: lambdaEdgeRole # required if you want to use 'serverless deploy --function' later on
        AssumeRolePolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Principal:
                Service:
                  - lambda.amazonaws.com
                  - edgelambda.amazonaws.com
              Action: sts:AssumeRole
        # note that these rights are needed if you want your function to be able to communicate with resources within your vpc
        ManagedPolicyArns:
          - arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole
        Policies:
          - PolicyName: serverless-framework-lambda-edge-policy
            PolicyDocument:
              Version: '2012-10-17'
              Statement:
                - Effect: Allow # note that these rights are given in the default policy and are required if you want logs out of your lambda(s)
                  Action:
                    - logs:CreateLogGroup
                    - logs:CreateLogStream
                    - logs:PutLogEvents
                  Resource:
                    - 'Fn::Join':
                      - ':'
                      -
                        - 'arn:aws:logs:*:*:*'

plugins:
  - serverless-lambda-edge-pre-existing-cloudfront
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: non-linux

```

Above is the sample `serverless.yml` file for reference, you could setup four stages in Lambda@Edge, such as `viewer-request` / `viewer-response` / `origin-request` / `origin-response`, to associate with Lambda with CloudFront distribution for customized logic.

In this example, I would like to setup the `Cache-Control` header to `max-age=60`, then I need to create a new function section in `serverless.yml` and input the existing CloudFront ID and other information.

As we can see in the bottom part of `serverless.yml`, we could leverage various plugins in the Serverless Framework. Thanks to [serverless-lambda-edge-pre-existing-cloudfront](https://github.com/serverless-operations/serverless-lambda-edge-pre-existing-cloudfront), we could involve the preexisting CLoudFront distribution in our `serverless.yml`, otherwise, we need to create a brand new CloudFront distribution in this project and we could not use the existing distribution we created before.

Next, we need to install the plugins we need in this project

```
$ npm install serverless-lambda-edge-pre-existing-cloudfront
$ npm install --save-dev serverless-python-requirements
```

After we settle everything above, we could handle the Lambda logic we need to involve in the project. We could move to `originResponse.py` or any python file you created to write your Lambda handler.

```
import json

def handler(event, context):
    response = event["Records"][0]["cf"]["response"]
    headers = response["headers"]

    cacheControlheader = 'Cache-Control';
    maxAge = 'max-age=60';

    headers[cacheControlheader.lower()] = [{
        'key': cacheControlheader,
        'value': maxAge
    }]

    print(f"Response header {cacheControlheader} was set to {maxAge}")
    return response

```

It is quite easy to add `Cache-Control` header value in Lambda@Edge and every request return by your origin will add `Cache-Control` header in your response.

Last but not least, we need to deploy our solution with `sls deploy` in the root folder.

## Reference
[serverless-lambda-edge-pre-existing-cloudfront](https://github.com/serverless-operations/serverless-lambda-edge-pre-existing-cloudfront)