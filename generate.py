import click
import requests
import json
import os
import re

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
    response = requests.get(url).json()
    version = response['version']
    metadata = response['metadata']
    operations = response['operations']
    shapes = response['shapes']
    output_file = re.sub('([a-z]+)([A-Z])', r'\1_\2', modulename).replace('.', '_').lower() + '.ex'
    with open(template, 'r') as readfile:
        doc = readfile.read()
    doc = doc.replace('$version', version)
    metadata_string = ''
    for key, value in metadata.items():
        metadata_string += '{}: {}\n\t'.format(key, value)
    doc = doc.replace('$metadata', metadata_string)
    service_name = re.sub('([a-z]+)([A-Z])', r'\1_\2', metadata['endpointPrefix']).replace('.', '_').lower()
    doc = doc.replace('$service', ':{}'.format(service_name))
    with open(output_file, 'w') as writefile:
        writefile.write(doc)


if __name__ == '__main__':
    cli()
