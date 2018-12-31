"""
Run this script to delete all existing data and recreate the indices.
If there was no data to begin with, it will just create the indices.
"""

import requests
from posixpath import join as urljoin

address = 'http://localhost:9200'


def print_res_status(res):
    if res.status_code == 200:
        print('Success.')
    elif res.status_code == 201:
        print('Added with success.')
    else:
        print('Something wrong, code {}'.format(res.status_code))


def delete_index(index_name):
    res = requests.delete(urljoin(address, index_name))
    print('Attempting deleting index {}...'.format(index_name), end=' ')
    print_res_status(res)


def get_mapping_namenindex():
    """Create a mapping dictionary for the namenindex."""
    mapping = {'properties': {}}
    for name in ['naam', 'inhoud', 'getuigen', 'datum', 'bron', 'bijzonderheden']:
        mapping['properties'][name] = _get_field('text', norms=False)
    mapping['properties']['naam_keyword'] = _get_field('keyword')
    mapping['properties']['jaar'] = _get_field('short')  # signed 16 bit integer
    return mapping


def get_mapping_maatboek_heemskerk():
    """Create a mapping dictionary for the namenindex."""
    mapping = {'properties': {}}
    for name in ['gebied', 'sector', 'nummer', 'oppervlakte', 'eigenaar', 'huurder',
                 'bedrag', 'jaar', 'bron', 'opmerkingen']:
        mapping['properties'][name] = _get_field('text', norms=False)
    return mapping


def _get_field(field_type, norms=None):
    """Create a dictionary describing a mapping datafield type and additional parameters."""
    field = {'type': field_type}
    if norms is not None:
        field['norms'] = norms
    return field


def create_index(index_name):
    res = requests.put(urljoin(address, index_name))
    print('Attempting putting new index {}...'.format(index_name), end=' ')
    print_res_status(res)


def put_mapping(index_name, mapping):
    res = requests.put(urljoin(address, index_name, '_mapping', 'doc'), json=mapping)
    print('Attempting putting mapping of index {}...'.format(index_name), end=' ')
    print_res_status(res)


def do_the_thing(name):
    if name == 'namenindex':
        mapping = get_mapping_namenindex()
    elif name == 'maatboek_heemskerk':
        mapping = get_mapping_maatboek_heemskerk()
    else:
        raise ValueError(f'Unexpected index name: {name}.')
    delete_index(name)
    create_index(name)
    put_mapping(name, mapping)


if __name__ == '__main__':
    assert requests.get(address).status_code == 200
    do_the_thing('namenindex')
    # do_the_thing('maatboek_heemskerk')
    print('Finished!')
