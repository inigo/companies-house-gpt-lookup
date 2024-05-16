import requests
from requests.auth import HTTPBasicAuth
import csv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os


class CompanyInformationRetriever:
    base_url = "https://api.company-information.service.gov.uk/company/"

    def __init__(self, api_key):
        self.api_key = api_key

    def retrieve_company(self, company_number):
        url = self.base_url + company_number
        response = requests.request("GET", url, auth=HTTPBasicAuth(self.api_key, ''))
        if response.status_code == 200:
            data = response.json()
            company_name = data.get('company_name')
            company_number = data.get('company_number')
            # parent_business_type = data.get('branch_company_details', {}).get('business_type')
            sic_codes = data.get('sic_codes', [])
            return company_name, company_number, sic_codes
        else:
            response.raise_for_status()

    def retrieve_companies(self, company_nos_array):
        [self.retrieve_company(company_no) for company_no in company_nos_array]


class SICCodeLookup:
    def __init__(self, csv_file):
        self.sic_dict = {}
        self._load_csv(csv_file)

    def _load_csv(self, csv_file):
        with open(csv_file, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header
            for row in reader:
                sic_code, description = row
                self.sic_dict[sic_code] = description

    def get_description(self, sic_code):
        return self.sic_dict.get(sic_code, "SIC code not found")


class CompanyInformation(BaseModel):
    company_name: str
    company_number: str
    sic_codes: list[str]
    sic_descriptions: list[str]


class CompanyInformationError(BaseModel):
    company_number: str
    error: str


class CompanyLookup:
    def __init__(self, company_information_retriever, sic_code_lookup):
        self.company_information_retriever = company_information_retriever
        self.sic_code_lookup = sic_code_lookup

    def lookup_company(self, company_number):
        company_number = company_number.strip().zfill(8)
        (company_name, company_number, sic_codes) = self.company_information_retriever.retrieve_company(company_number)
        sic_descriptions = [self.sic_code_lookup.get_description(code) for code in sic_codes]
        return CompanyInformation(
            company_name=company_name,
            company_number=company_number,
            sic_codes=sic_codes,
            sic_descriptions=sic_descriptions)


class CompanyAPI:
    def __init__(self, company_lookup: CompanyLookup, root_path: str = "/"):
        self.company_lookup = company_lookup
        self.app = FastAPI(root_path=root_path)

        self.app.get("/")(self.read_root)
        self.app.add_api_route(
            "/company/{company_id}",
            self.get_company_details,
            methods=["GET"],
            response_model=CompanyInformation,
            summary="Get Company Details",
            description="Retrieve details for a single company using a company number.",
            response_description="The details of the company, including its name, company number, the SIC codes for its activities and their descriptions.",
        )
        self.app.add_api_route(
            "/companies/",
            self.get_companies_details,
            methods=["GET"],
            response_model=list[CompanyInformation | CompanyInformationError],
            summary="Get Multiple Company Details",
            description="Retrieve details for multiple companies, using a comma-separated list of company numbers.",
            response_description="The details of each company, including its name, company number, the SIC codes for its activities and their descriptions; or an error entry for any companies that failed",
        )

    def get_company_details(self, company_id: str):
        try:
            company_info = self.company_lookup.lookup_company(company_id)
            return company_info
        except requests.HTTPError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))

    def get_companies_details(self,
                              company_ids: str = Query(
                                  ...,
                                  pattern=r'^([a-zA-Z0-9]+,)*[a-zA-Z0-9]+$',
                                  description="Comma-separated list of company IDs")
                              ):
        company_id_list = company_ids.split(',')
        results = []

        for company_number in company_id_list:
            try:
                company_info = self.company_lookup.lookup_company(company_number)
                results.append(company_info)
            except requests.HTTPError as e:
                results.append(CompanyInformationError(
                    company_number=company_number,
                    error=str(e)
                ))

        if not results:
            raise HTTPException(status_code=400, detail="All company number lookups failed")

        return results

    @staticmethod
    def read_root():
        return {"message": "Company lookup service is working - see /docs for Swagger documentation"}


if __name__ == '__main__':
    load_dotenv() # Add API_KEY=whatever to a .env file
    port = os.getenv("PORT") or 8000
    # API key provided by Companies House - see https://developer.company-information.service.gov.uk/
    api_key = os.getenv("API_KEY")
    root_path = os.getenv("ROOT_PATH") or ""

    company_retriever = CompanyInformationRetriever(api_key)
    # CSV is downloaded from https://assets.publishing.service.gov.uk/media/5a7f8639e5274a2e87db65e1/SIC07_CH_condensed_list_en.csv/
    sic_lookup = SICCodeLookup('SIC07_CH_condensed_list_en.csv')
    company_lookup = CompanyLookup(company_retriever, sic_lookup)
    company_api = CompanyAPI(company_lookup, root_path)

    app = company_api.app
    uvicorn.run(app, host="0.0.0.0", port=port)
