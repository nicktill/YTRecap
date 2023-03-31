import boto3
import sagemaker
from sagemaker.huggingface.model import HuggingFaceModel

hub = {
  'HF_MODEL_ID':'facebook/bart-large-cnn', 
  'HF_TASK':'summarization'
}

huggingface_model = HuggingFaceModel(
   env=hub,                                                
   role=sagemaker.get_execution_role(),                                        
   transformers_version='4.12.3',                           
   pytorch_version='1.9.1',                                
   py_version='py38'    
)

predictor = huggingface_model.deploy(
   initial_instance_count=1,
   instance_type="ml.m5.xlarge"
)

output = predictor.predict({'inputs': 'The U.S. economy added 943,000 jobs in July, well above the expected 870,000, as the unemployment rate fell to 5.4 percent, the Labor Department said Friday. The report showed strong gains in leisure and hospitality, local government education, and professional and business services. However, the number of people out of work for at least 27 weeks rose slightly to 3.4 million.'})
print(output)
# [{'summary_text': 'The U.S. economy added 943,000 jobs in July, well above the expected 870,000. The unemployment rate fell to 5.4 percent, the Labor Department said Friday. The report showed strong gains in leisure and hospitality, local government education, and professional and business services.'}]
