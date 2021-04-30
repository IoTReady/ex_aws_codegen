# ex_aws_codegen

An attempt at parsing api-*.json files from [official AWS SDKs](https://github.com/aws/aws-sdk-go/blob/main/models/apis/iot/2015-05-28/api-2.json) and generating usable Elixir modules built on top of [ExAws](https://hexdocs.pm/ex_aws/readme.html).

## Usage

- Create virtual environment: `python3 -m venv venv`
- Enter virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run the generator, e.g. `python generate.py parse --modulename ExAws.Iot --url https://raw.githubusercontent.com/aws/aws-sdk-go/main/models/apis/iot/2015-05-28/api-2.json`

## Status

- [x] Generate type specs for all parameters (`shapes`)
- [x] Generate RestQuery modules that compile without errors
- [ ] Test functions
- [ ] Add tests
- [ ] Port to JSON modules
