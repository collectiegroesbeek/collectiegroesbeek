

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

