import click
import requests
import json
import os
import re

default_template = 'template.ex'

all_types = {}

@click.group()
def cli():
    pass


@cli.command()
@click.option('--template', default=default_template, help='Template to use for generated Elixir code.')
@click.option('--modulename', prompt="Module Name", help='Module name to use for generated Elixir module e.g. Bodh.Iot')
@click.option('--url', prompt="JSON URL", help='JSON URL to parse.')
def parse(template, modulename, url):
    """Download JSON from URL and parse."""
    output_file = get_snake_case(modulename) + '.ex'
    with open(template, 'r') as readfile:
        doc = readfile.read()
    response = requests.get(url).json()
    doc = doc.replace('$modulename', modulename)
    doc = insert_version(doc, version = response['version'])
    doc = insert_metadata(doc, response['metadata'])
    doc = insert_types(doc, response['shapes'])
    doc = insert_functions(doc, response['operations'], response['shapes'])
    with open(output_file, 'w') as writefile:
        writefile.write(doc)

def get_snake_case(str):
    return re.sub('([a-z]+)([A-Z])', r'\1_\2', str).replace('.', '_').lower()

def get_elixir_type(aws_type):
    type_mapping = {
        'blob': 'blob', 
        'boolean': 'boolean', 
        'double': 'float', 
        'integer': 'integer', 
        'long': 'integer', 
        'map': 'map', 
        'string': 'binary', 
        'timestamp': 'integer' # assuming these are unix timestamps
    }
    return type_mapping.get(aws_type) or get_snake_case(aws_type)

def get_http_method(http_method):
    methods_mapping = {
        'GET': ':get',
        'POST': ':post',
        'PUT': ':put',
        'PATCH': ':patch',
        'DELETE': ':delete',
    }
    return methods_mapping[http_method]

def insert_version(doc, version):
    return doc.replace('$version', version)

def insert_metadata(doc, metadata):
    metadata_string = ''
    for key, value in metadata.items():
        metadata_string += '#\t{}: {}\n\t'.format(key, value)
    doc = doc.replace('$metadata', metadata_string)
    service_name = get_snake_case(metadata['endpointPrefix'])
    return doc.replace('$service', ':{}'.format(service_name))

def insert_types(doc, shapes, only_required = True):
    type_template = """\n\t@type $type_name :: $type_value\n"""
    all_types_string = ''
    complex_types = ['list', 'structure']
    for k,v in shapes.items():
        type_name = get_snake_case(k)
        type_string = type_template.replace('$type_name', type_name)
        aws_type = v['type']
        if aws_type not in complex_types:
            # basic types
            elixir_type = get_elixir_type(aws_type)
            type_string = type_string.replace('$type_value', elixir_type)
            all_types[type_name] = elixir_type
        elif aws_type == 'list':
            element_type = v['member']['shape']
            elixir_type = get_elixir_type(element_type)
            type_string = type_string.replace('$type_value', '[{}]'.format(elixir_type))
            all_types[type_name] = elixir_type
        elif aws_type == 'structure':
            if only_required:
                if v.get('required'):
                    struct = '%{'
                    for key in v['required']:
                        value = get_snake_case(v['members'][key]['shape'])
                        struct += key + ': ' + value + ', '
                    struct = struct[:-2] + '}'
                else:
                    struct = '%{}'
            else:
                if len(v['members']):
                    struct = '%{'
                    for key,b in v['members'].items():
                        value = get_snake_case(b['shape'])
                        struct += key + ': ' + value + ', '
                    struct = struct[:-2] + '}'
                else:
                    struct = '%{}'
            type_string = type_string.replace('$type_value', struct)
            all_types[type_name] = struct
        else:
            print(k,v)
            continue
        all_types_string += type_string
    return doc.replace('$types', all_types_string)

def insert_functions(doc, operations, shapes):
    function_template = """\n\t@spec $func_name($input_type) :: $output_type\n\tdef $func_name($param_list = params) do\n\t%{@query | http_method: $http_method, path: "$uri", params: params} |> execute()\n\tend\n"""
    all_functions = ''
    for op in operations.values():
        func_name = get_snake_case(op['name'])
        func_string = function_template.replace('$func_name', func_name)
        output_type = op.get('output')
        if output_type:
            output_type = get_snake_case(output_type['shape'])
            func_string = func_string.replace('$output_type', output_type)
        else:
            func_string = func_string.replace('$output_type', 'nil')
        input_type = get_snake_case(op['input']['shape'])
        func_string = func_string.replace('$input_type', input_type)
        func_string = func_string.replace('$param_list', all_types[input_type])
        http_method = op['http']['method']
        func_string = func_string.replace('$http_method', get_http_method(http_method))
        uri = op['http']['requestUri']
        # not sure why some uris have a + in the param list (for multiple?)
        uri = uri.replace('+', '')
        uri = re.split("[{}]", uri)
        uri = [part for part in uri if part]
        uri = ["#{"+get_snake_case(part)+"}" if not part.startswith('/') else part for part in uri]
        uri = ''.join(uri)
        func_string = func_string.replace('$uri', uri)
        all_functions += func_string

    return doc.replace('$functions', all_functions)


if __name__ == '__main__':
    cli()
    print(all_types)
