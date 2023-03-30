import boto3
import json
import os

ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
SESSION_TOKEN = os.environ.get('SESSION_TOKEN')


session = boto3.Session(
    aws_access_key_id='ACCESS_KEY',
    aws_secret_access_key='SECRET_KEY',
    aws_session_token='SESSION_TOKEN',
    region_name='us-east-2'
)

runtime = session.client("sagemaker-runtime")
runtime = boto3.client("sagemaker-runtime", region_name="us-east-2")
endpoint_name = "huggingface-pytorch-inference-2023-03-29-21-31-55-850"
content_type = "application/json"
input_text = "These are the closed captions that you want your model to summarize."

payload = json.dumps({"inputs": input_text})
response = runtime.invoke_endpoint(
    EndpointName=endpoint_name,
    ContentType=content_type,
    Body=payload
)

# Extract the summarized text from the response
response_body = json.loads(response["Body"].read().decode("utf-8"))
print(response_body)