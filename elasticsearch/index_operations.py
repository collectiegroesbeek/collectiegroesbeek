import openpyxl
import json
import requests

address = 'http://localhost:9200'


def print_res_status(res):
    if res.status_code == 200:
        print('Success.')
    elif res.status_code == 201:
        print('Added with success.')
    else:
        print('Something wrong, code {}'.format(res.status_code))


def delete_index(index_name):
    res = requests.delete(address + '/' + index_name)
    print('Attempting deleting index {}...'.format(index_name), end=' ')
    print_res_status(res)


def get_mapping_namenindex():
    """Create a mapping dictionary for the namenindex."""
    mapping = {'properties': {}}
    for name in ['naam', 'inhoud', 'getuigen', 'datum', 'bron', 'bijzonderheden']:
        mapping['properties'][name] = _get_field('text', norms=False)
    mapping['properties']['naam_keyword'] = _get_field('keyword')
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
    res = requests.put(address + '/' + index_name)
    print('Attempting putting new index {}...'.format(index_name), end=' ')
    print_res_status(res)


def put_mapping(index_name, mapping):
    res = requests.put(address + '/' + index_name + '/_mapping/doc', json=mapping)
    print('Attempting putting mapping of index {}...'.format(index_name), end=' ')
    print_res_status(res)


if __name__ == '__main__':
    name_index = 'namenindex'
    mapping = get_mapping_namenindex()
    delete_index(name_index)
    create_index(name_index)
    put_mapping(name_index, mapping)

    name_index = 'maatboek_heemskerk'
    mapping = get_mapping_maatboek_heemskerk()
    delete_index(name_index)
    create_index(name_index)
    put_mapping(name_index, mapping)
    print('Finished!')

