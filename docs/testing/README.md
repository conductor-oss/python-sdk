# Testing Workflows

## Unit Testing

You can unit test your workflow on a remote server by using the testWorkflow method.
A sample unit test code snippet is provided below.

### Sample Workflow JSON
[calculate_loan_workflow.json](../../tests/integration/resources/test_data/calculate_loan_workflow.json)
### Sample Task Input / Output
[loan_workflow_input.json](../../tests/integration/resources/test_data/loan_workflow_input.json)

### Sample Unit Test

```python
import json
from conductor.shared.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models import WorkflowTestRequest
from conductor.client.orkes.orkes_workflow_client import OrkesWorkflowClient

TEST_WF_JSON_PATH = 'tests/integration/resources/test_data/calculate_loan_workflow.json'
TEST_IP_JSON_PATH = 'tests/integration/resources/test_data/loan_workflow_input.json'

auth = AuthenticationSettings(key_id=KEY_ID, key_secret=KEY_SECRET)
config = Configuration(server_api_url=SERVER_API_URL, authentication_settings=auth)
api_client = ApiClient(configuration)
workflow_client = OrkesWorkflowClient(configuration)

f = open(TEST_WF_JSON_PATH, "r")
workflowJSON = json.loads(f.read())
workflowDef = api_client.deserialize_class(workflowJSON, "WorkflowDef")

f = open(TEST_IP_JSON_PATH, "r")
inputJSON = json.loads(f.read())

testRequest = WorkflowTestRequest(name=workflowDef.name, workflow_def=workflowDef)

testRequest.input = {
    "userEmail": "user@example.com",
    "loanAmount": 11000,
}

testRequest.name = workflowDef.name
testRequest.version = workflowDef.version
testRequest.task_ref_to_mock_output = testTaskInputs

execution = workflow_client.test_workflow(testRequest)
assert execution != None

# Ensure workflow is completed successfully
assert execution.status == "COMPLETED"

# Ensure the inputs were captured correctly
assert execution.input["loanAmount"] == testRequest.input["loanAmount"]
assert execution.input["userEmail"] == testRequest.input["userEmail"]

# A total of 7 tasks were executed
assert len(execution.tasks) == 7

fetchUserDetails = execution.tasks[0]
getCreditScore = execution.tasks[1]
calculateLoanAmount = execution.tasks[2]
phoneNumberValidAttempt1 = execution.tasks[4]
phoneNumberValidAttempt2 = execution.tasks[5]
phoneNumberValidAttempt3 = execution.tasks[6]

# fetch user details received the correct input from the workflow
assert fetchUserDetails.input_data["userEmail"] == testRequest.input["userEmail"]

userAccountNo = 12345
# And that the task produced the right output
assert fetchUserDetails.output_data["userAccount"] == userAccountNo

# get credit score received the right account number from the output of the fetch user details
assert getCreditScore.input_data["userAccountNumber"] == userAccountNo

# The task produced the right output
expectedCreditRating = 750
assert getCreditScore.output_data["creditRating"] == expectedCreditRating

# Calculate loan amount gets the right loan amount from workflow input
expectedLoanAmount = testRequest.input["loanAmount"]
assert calculateLoanAmount.input_data["loanAmount"] == expectedLoanAmount

# Calculate loan amount gets the right credit rating from the previous task
assert calculateLoanAmount.input_data["creditRating"] == expectedCreditRating

authorizedLoanAmount = 10_000
assert calculateLoanAmount.output_data["authorizedLoanAmount"] == authorizedLoanAmount

assert not phoneNumberValidAttempt1.output_data["valid"]
assert not phoneNumberValidAttempt2.output_data["valid"]
assert phoneNumberValidAttempt3.output_data["valid"]

# Finally, lets verify the workflow outputs
assert execution.output["accountNumber"] == userAccountNo
assert execution.output["creditRating"] == expectedCreditRating
assert execution.output["authorizedLoanAmount"] == authorizedLoanAmount

# Workflow output takes the latest iteration output of a loopOver task.
assert execution.output["phoneNumberValid"]
```
