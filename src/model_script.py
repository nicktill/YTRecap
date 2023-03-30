import boto3
import json
from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env file

ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID') # Get the access key from the environment variables
SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') # Get the secret key from the environment variables

session = boto3.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-2'
)

runtime = session.client("sagemaker-runtime") # Create a SageMaker runtime client
endpoint_name = "huggingface-pytorch-inference-2023-03-29-21-31-55-850" # The name of the endpoint that you created
content_type = "application/json" # The MIME type of the input data in the request body
input_text = "These are the closed captions that you want your model to summarize." # The text that you want to summarize

payload = json.dumps({"inputs": input_text}) # Create the payload that you will send to the endpoint
response = runtime.invoke_endpoint( # Invoke the endpoint
    EndpointName=endpoint_name, 
    ContentType=content_type, 
    Body=payload
)

# Extract the summarized text from the response
response_body = json.loads(response["Body"].read().decode("utf-8")) 
print(response_body)
