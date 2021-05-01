import click
import requests
import json
import os
import re
import subprocess
from jinja2 import Template

default_template = 'template.ex'

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
    response = requests.get(url).json()
    context = {}
    context['modulename'] = modulename
    context['version'] = response['version']
    context['metadata'] = response['metadata']
    context['servicename'] = get_snake_case(response['metadata']['endpointPrefix'])
    context['types'] = parse_shapes(response['shapes'])
    context['functions'] = parse_operations(response['operations'], context['types'])
    with open(template, 'r') as f:
        jinja_template = Template(f.read())
        out = jinja_template.render(context)
        with open(output_file, 'w') as wf:
            wf.write(out)
    subprocess.run(["mix", "format", output_file])

def get_snake_case(str):
    return re.sub('([a-z]+)([A-Z])', r'\1_\2', str).replace('.', '_').lower()

def get_elixir_type(aws_type):
    type_mapping = {
        'blob': 'binary', 
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

def parse_shapes(shapes, only_required = False):
    all_types = {}
    built_in_types = ['binary', 'boolean', 'float', 'integer', 'map', 'string', 'number', 'port']
    complex_types = ['list', 'structure']
    for k,v in shapes.items():
        type_name = get_snake_case(k)
        if type_name in built_in_types or type_name in all_types:
            # Do not redefine elixir's built-in types or previously defined types
            continue
        aws_type = v['type']
        if aws_type not in complex_types:
            # basic shapes
            all_types[type_name] = {'shape': 'basic', 'def': get_elixir_type(aws_type)}
        elif aws_type == 'list':
            element_type = v['member']['shape']
            all_types[type_name] = {'shape': 'list', 'def': get_elixir_type(element_type)}
        elif aws_type == 'structure':
            all_types[type_name] = {'shape': 'structure', 'def': {}}
            keys = []
            if only_required and v.get('required'):
                keys = v['required']
            elif len(v['members']):
                keys = list(v['members'].keys())
            for key in keys:
                try:
                    value = get_snake_case(v['members'][key]['shape'])
                    all_types[type_name]['def'][key] = value
                except:
                    print("keys", keys)
                    print(k,v, key)
        else:
            print(k,v)
            continue
        
    return all_types

def get_param_name(all_types, input_type, param_id):
    try:
        return all_types[input_type]['def'][param_id]
    except:
        # Edge case for IoT service
        # param is named 'caCertificateId' but the definition uses 'certificate_id'
        # print(input_type, param_id, all_types[input_type])
        if param_id == 'caCertificateId':
            return 'certificate_id'
        else:
            print(input_type, param_id, all_types[input_type])
            return ''

def parse_operations(operations, all_types):
    all_functions = {}
    for op in operations.values():
        func_name = get_snake_case(op['name'])
        input_type = get_snake_case(op['input']['shape'])
        output_type = (op.get('output') and get_snake_case(op['output']['shape'])) or "nil"
        # not sure why some uris have a + in the param list (for multiple?)
        # This trips up the Elixir compiler - convert to list?
        uri = op['http']['requestUri'].replace('+', '')
        # clean out empty strings and isolate params
        uri = [part for part in re.split("[{}]", uri) if part]
        uri = ["#{"+get_param_name(all_types, input_type, param_id)+"}" if not param_id.startswith('/') else param_id for param_id in uri]
        uri = ''.join(uri)
        all_functions[func_name] = {
            'input_type': input_type,
            'output_type': output_type,
            'params': all_types[input_type]['def'],
            'http_method': get_http_method(op['http']['method']),
            'uri': uri,
        }
    return all_functions

if __name__ == '__main__':
    cli()
