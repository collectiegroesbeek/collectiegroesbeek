from branca.element import MacroElement
from jinja2 import Template

from folium.elements import JSCSSMixin


class OpacityControl(JSCSSMixin, MacroElement):
    _template = Template(
        """
        {% macro script(this, kwargs) %}
            L.control.opacity({ "{{ this.layer_name }}": {{ this.layer.get_name()}} }, {
                label: 'transparantie',
            }).addTo({{ this._parent.get_name() }});
        {% endmacro %}
    """
    )

    default_js = [
        (
            "Leaflet.Control.Opacity",
            "https://cdn.jsdelivr.net/npm/leaflet.control.opacity@1.6.0/dist/L.Control.Opacity.min.js",
        )
    ]

    default_cs = [
        (
            "Leaflet.Control.Opacity",
            "https://cdn.jsdelivr.net/npm/leaflet.control.opacity@1.6.0/dist/L.Control.Opacity.min.css",
        )
    ]

    def __init__(self, layer):
        super().__init__()
        self.layer = layer
