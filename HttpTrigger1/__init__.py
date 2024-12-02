import logging
import os
import json
import azure.functions as func
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

import random
import string

def generate_random_string(length):
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

endpoint = os.getenv("AZURE_DOC_INTEL_ENDPOINT")
api_key = os.getenv("AZURE_DOC_INTEL_KEY")

# base model for selections
class Selection(BaseModel):
    Selection: str = Field(
        ..., description="The selection of the key-value pair", example="selection"
        )

# base model for key value pairs
class KeyValuePair(BaseModel):
    question_number: Optional[str] = Field(
        None, description="Question number from the original document", example="1"
        )
    key: str = Field(
        ..., description="The key of the key-value pair", example="key"
        )
    value: str = Field(
        ..., description="The value of the key-value pair", example="value"
        )
    notes: Optional[str] = Field(
        None, description="Notes in the document for the key-value pair", example="notes"
        )
# base model for CheckListSubSection
class ChecklistSubSection(BaseModel):
    title: str = Field(
        ..., description="The title of the checklist sub-section", example="sub-section title"
        )
    items: List[KeyValuePair] = Field(
        ..., description="The items in the checklist sub-section", example=[{"key": "key", "value": "value"}]
        )

# base model for Checklist sections
class ChecklistSection(BaseModel):
    title: str = Field(
        ..., description="The title of the checklist section", example="section title"
        )
    summary: str = Field(
        ..., description="Summarize the data included in the section. Create narrative", example="section summary"
        )
    # items: List[KeyValuePair] = Field(
    #     ..., description="The items in the checklist section", example=[{"key": "key", "value": "value"}]
    #     )
    subsections: List[ChecklistSubSection] = Field(
        ..., description="The subsections in the checklist section", example=[{"title": "sub-section title", "items": [{"key": "key", "value": "value"}]}]
        )


# Model for the entire Checklist
class Checklist(BaseModel):
    summary: str = Field(
        ..., description="Narrative summary of the overall data in the document.", example="checklist summary"
        )
    sections: List[ChecklistSection] = Field(
        ..., description="The sections of the checklist", example=[
            {
                "title": "section title 1",
                "items": [{"number":"1", "key": "key1", "value": "value1", "notes": "notes"}]
            },
            {
                "title": "section title 2",
                "items": [{"number":"1", "key": "key2", "value": "value2", "notes": "notes"}]
            }
        ]
    )
    original_document: str = Field(
        ..., description="For future use, leave blank", example="NULL"
        )
    file_name: str = Field(
        ..., description="Generate unique filename with location and date information from the content", example="bangkok_august_2021qdhjhqwp[]"
        )






def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Azure Function triggered to process document.')

    # Retrieve the document from the request (assuming it's sent as binary content)
    try:
        document_content = req.get_body()
        if not document_content:
            # Load test document if no content is provided
            with open("./HttpTrigger1/example.pdf", "rb") as f:
                document_content = f.read()
    #         raise ValueError("No document content found in the request.")
    except Exception as e:
        logging.error(f"Error reading document content: {e}")
        return func.HttpResponse(
            f"Error reading document content: {e}",
            status_code=400
        )

    # Create the client
    document_client = DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )

    # Analyze the document
    try:
        poller = document_client.begin_analyze_document(
            "prebuilt-document",
            document_content
        )
        result = poller.result()
    except Exception as e:
        logging.error(f"Error during document analysis: {e}")
        return func.HttpResponse(
            f"Error during document analysis: {e}",
            status_code=500
        )

    # Extract key-value pairs
    kv_dict = {}
    if hasattr(result, 'key_value_pairs'):
        for kv_pair in result.key_value_pairs:
            if kv_pair.key and kv_pair.value:
                key_text = kv_pair.key.content
                value_text = kv_pair.value.content
                kv_dict[key_text] = value_text

    # Aggregate text content
    text_content = ""
    if hasattr(result, 'pages'):
        for page in result.pages:
            for line in page.lines:
                text_content += line.content + " "

    # Prepare the response
    response_data = {
        "key_value_pairs": kv_dict,
        "text_content": text_content.strip()
    }


    # Initialize Azure OpenAI
    llm = AzureChatOpenAI(
        azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        temperature=0,
        top_p=1.0,
        verbose=True,
        azure_endpoint=os.getenv('AZURE_OPENAI_API_BASE')
    )


    prompttemplate = """
         You are a financial expert AI that assists with the creation of reports based on review of financial offices across the organization. 
        Provided below is a report detailing an inperson review / audit from a recent visit to a location. 

        Key Vaule Pairs:

        {KeyVaulePairs}

        Full Text:

        {input}

        - Include all of the individual items in each section.
        - Complete a summary of the responses in the section to assist with creating a narrative.
        - Extract any additional information from each question and add it as a note.
        - If a question includes additional selection boxes include those as selections in list in the output.
        - Add additional information for any localization for the country the office is located in.
    """

    prompt = ChatPromptTemplate.from_template(prompttemplate)
    structured_output = llm.with_structured_output(Checklist)
    results = structured_output.invoke(
        prompt.invoke(
            {
                "input": response_data["text_content"],
                "KeyVaulePairs": response_data["key_value_pairs"]
            }
        )
    )

    ## Summary Prompt - Generate a more detailed summary of the cashier report
    summaryPrompTemplate = """
        Review the provided JSON and provide a summary of the site visit. 
        Be verbose and cover all of the topics mentioned in the JSON.
        JSON:

        {JSON}

        Only provide the summary, do not include any additional information.
    """
    summaryPrompt = ChatPromptTemplate.from_template(summaryPrompTemplate)
    summary = llm.invoke(summaryPrompt.invoke({"JSON": results}))





    # Update the results    
    results.summary = summary.content
    results.original_document = response_data
    results.file_name = results.file_name + generate_random_string(10)

    blobService = BlobServiceClient(
        account_url=os.getenv('AZURE_BLOB_ENDPOINT'),
        credential=os.getenv('AZURE_BLOB_KEY')
    )
    # Upload JSON
    blob = BlobClient(
        account_url=os.getenv('AZURE_BLOB_ENDPOINT'),
        credential=os.getenv('AZURE_BLOB_KEY'),
        container_name=os.getenv('AZURE_BLOB_CONTAINER_NAME'),
        blob_name=results.file_name + ".json"
    )
    blob.upload_blob(
        json.dumps(results.dict(), ensure_ascii=False, indent=2),
        content_settings=ContentSettings(content_type='application/json'),
        )
    
    # Upload PDF
    blob = BlobClient(
        account_url=os.getenv('AZURE_BLOB_ENDPOINT'),
        credential=os.getenv('AZURE_BLOB_KEY'),
        container_name=os.getenv('AZURE_BLOB_CONTAINER_NAME'),
        blob_name=results.file_name + ".pdf"
    )
    blob.upload_blob(
        document_content,
        content_settings=ContentSettings(content_type='application/pdf'),
        )

    # Return the response
    return func.HttpResponse(
        #json.dumps(response_data, ensure_ascii=False, indent=2),
        json.dumps(results.dict(), ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200
    )
