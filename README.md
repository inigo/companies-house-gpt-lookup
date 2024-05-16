Companies House company ID lookup via a ChatGPT action

## Usage

To use:

* Register for a Companies House API key via https://developer.company-information.service.gov.uk/
* Add the key to a .env file with the format API_KEY=xxx
* Create a virtual environment with `python -m venv .venv`, and switch to it with `source .venv/bin/activate`
* Install requirements with `pip install -r requirements.txt`
* Run with `.venv/bin/python main.py`
* Go to http://localhost:8000/docs

## GPT setup

To set up in ChatGPT:

* Set it running somewhere publicly available (you may need to use the ROOT_PATH variable to specify the public URL)
* Within a (paid-for) ChatGPT account, create a new GPT
* In the Actions, create an action, and import the schema from (your url)/openapi.json
* In the Prompt, tell ChatGPT to use the action when it sees a company number.

## License
Copyright (C) 2024 Inigo Surguy

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.