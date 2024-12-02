# AI Cash Report Processing Function

This project is an Azure Function that processes cash report documents using Azure Form Recognizer and Azure OpenAI services. It extracts key-value pairs and text content from uploaded documents and generates structured data, which is then stored in Azure Blob Storage.

## Features

- Processes PDF documents to extract textual and structured data.
- Uses Azure Form Recognizer to analyze documents.
- Utilizes Azure OpenAI to generate structured outputs based on extracted data.
- Stores the processed data in JSON format in Azure Blob Storage.
- Uploads the original PDF document to Azure Blob Storage.

## Prerequisites

- Azure Account with access to:
  - Azure Functions
  - Azure Form Recognizer resource
  - Azure OpenAI Service
  - Azure Blob Storage
- Python 3.8 or higher
- [Azure Functions Core Tools](https://docs.microsoft.com/azure/azure-functions/functions-run-local)

## Setup

1. **Clone the repository**:

2. **Navigate to the project directory**

```bash
cd az_ai_gov-docai-example
```

3. **Install the required Python packages:**

```bash
pip install -r ./requirements.txt
```

4. **Configure environmental variables:**

- Update *local.settings.json* with your Azure service keys and endpoints. Leave the original function specific settings in place.

```json
  "Values": {
    "AZURE_OPENAI_DEPLOYMENT": "<your_openai_deployment_name>",
    "AZURE_OPENAI_API_BASE": "<your_openai_api_base>",
    "AZURE_OPENAI_API_KEY": "<your_openai_api_key>",
    "OPENAI_API_VERSION": "2023-05-15",
    "AZURE_DOC_INTEL_ENDPOINT": "<your_form_recognizer_endpoint>",
    "AZURE_DOC_INTEL_KEY": "<your_form_recognizer_key>",
    "AZURE_BLOB_ENDPOINT": "<your_blob_endpoint>",
    "AZURE_BLOB_KEY": "<your_blob_storage_key>",
    "AZURE_BLOB_CONTAINER_NAME": "<your_blob_container_name>"
  }
```

## Running the Function Locally

1. **Start the Azure Function**

```bash
func start
```

2. **Test the function by sending a POST with a PDF document**

- Using Powershell

```powershell
# Read the binary content of the file
$BinaryData = [System.IO.File]::ReadAllBytes("C:\path\to\your\document.pdf")

# Set the headers (omit "x-functions-key" if not required locally)
$Headers = @{
    "Content-Type" = "application/octet-stream"
}

# Make the POST request
$response = Invoke-RestMethod -Uri "http://localhost:7071/api/ProcessDocument" `
    -Method Post `
    -Headers $Headers `
    -Body $BinaryData

# Output the response
$response
```

- Using curl:

```bash
curl -X POST \
  -H "Content-Type: application/octet-stream" \
  --data-binary @"path/to/your/document.pdf" \
  http://localhost:7071/api/ProcessDocument
```

- Replace "C:\path\to\your\document.pdf" or "/path/to/your/document.pdf" with the actual path to you document.
- for local testing the *x-functions-key* is not required. 

## Deploying to Azure

1. **login to Azure:**

```bash
az login
```

2. **Deploy the Azure Function App:**

```bash
func azure functionapp publish <FuntionAppName> --publish-local-settings  
```

*note: the '--publish-local-settings' switch will automatically copy environmental variables from the local.settings.json into the configuration of the function app.*


## Usage

- Send HTTP POST requests to the deployed Azure Function URL with your PDF documents to process them.
- The function processes the docuemnt and uploads the results to the specified Azure Blob storage container.