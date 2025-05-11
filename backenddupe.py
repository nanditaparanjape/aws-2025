import json
import boto3
import botocore
region = "us-west-2"

# Create Bedrock client
bedrock = boto3.client(service_name='bedrock-runtime', region_name=region)

# Model IDs
MODELS = {
    "Claude 3.7 Sonnet": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "Claude 3.5 Haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "Amazon Nova Pro": "amazon.nova-pro-v1:0",
    "Amazon Nova Micro": "amazon.nova-micro-v1:0",
    "DeepSeek-R1": "deepseek.r1-v1:0",
    "Meta Llama 3.1 70B Instruct": "meta.llama3-1-70b-instruct-v1:0"
}

# Display function (optional)
def display_response(response, model_name=None):
    if model_name:
        print(f"\n=== Response from {model_name} ===\n")
    print(response)

#input text
ex_initial_data = """Blinding Lights, The Weeknd"""

#prompt
ex_prompt = """Based on the song provided, please give me the BPM, Key, Valence and Duration of the song"""

def editable_prompt_function(initial_data, prompt):
    full_prompt = f"""{prompt}
    <text>
    {initial_data}
    </text>
    """

    # Request body for Claude 3.7 Sonnet
    claude_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.5,
        "top_p": 0.9,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ],
    }

    # Make request
    try:
        response = bedrock.invoke_model(
            modelId=MODELS["Claude 3.7 Sonnet"],
            body=json.dumps(claude_body),
            accept="application/json",
            contentType="application/json"
        )
        # Parse body
        response_body = json.loads(response['body'].read())
        summary = response_body['content'][0]['text']
        display_response(summary, "Claude 3.7 Sonnet")

    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'AccessDeniedException':
            print(f"\n[ACCESS DENIED] {error.response['Error']['Message']}")
            print("Check IAM permissions and policies for Bedrock.\n")
            print("More help: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html")
        else:
            raise
