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

   