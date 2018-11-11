import flask

from . import app
from . import controller


@app.route('/')
def home():
    q = flask.request.args.get('q')
    return index() if not q else search()


def index():
    return flask.render_template(
        'index.html',
        show_search=controller.is_elasticsearch_reachable(),
    )


@app.route('/zoek')
def search():
    q: str = flask.request.args.get('q')
    if not q:
        return flask.render_template(
            'search.html',
            show_search=controller.is_elasticsearch_reachable(),
        )
    elif len(q) <= 2:
        return show_names_list(q)
    cards_per_page = 10
    page = flask.request.args.get('page', default=1, type=int)
    query, keywords = controller.get_query(q.lower())
    r = controller.post_query(query, index='namenindex', start=(page - 1) * cards_per_page,
                              size=cards_per_page)
    res, hits_total = controller.handle_results(r, keywords,
                                                keys=['naam', 'datum', 'inhoud', 'getuigen',
                                                      'bron', 'bijzonderheden'])
    page_range = controller.get_page_range(hits_total, page, cards_per_page)
    query_string = f'?q={q}&page='
    return flask.render_template('cards.html', hits=res,
                                 hits_total=hits_total,
                                 query_string=query_string,
                                 page_range=page_range, page=page)


@app.route('/namen')
def show_names_list(q):
    for letter in q.lower():
        if not letter.isalpha():
            return index()
    names_list = controller.get_names_list(q)
    hits_total = len(names_list)
    return flask.render_template('names.html', namen=names_list, hits_total=hits_total)


@app.route('/maatboek_heemskerk')
def search_maatboek_heemskerk():
    q = flask.request.args.get('q')
    if not q:
        return flask.render_template('maatboek_heemskerk.html', hits=[], hits_total=0,
                                     query_string='', page_range=[], page=1)
    cards_per_page = 10
    page = flask.request.args.get('page', default=1, type=int)
    query = {'multi_match': {'query': q.lower(),
                             'fields': ['gebied', 'sector', 'eigenaar', 'huurder', 'bron']}}
    keywords = q.lower().split(' ')
    r = controller.post_query(query, index='maatboek_heemskerk', start=(page - 1) * cards_per_page,
                              size=cards_per_page)
    res, hits_total = controller.handle_results(
        r,
        keywords,
        keys=['gebied', 'sector', 'nummer', 'oppervlakte', 'eigenaar', 'huurder', 'bedrag',
              'jaar', 'bron', 'opmerkingen']
    )
    page_range = controller.get_page_range(hits_total, page, cards_per_page)
    query_string = u'?q={}&page='.format(q)
    return flask.render_template('maatboek_heemskerk.html', hits=res,
                                 hits_total=hits_total,
                                 query_string=query_string,
                                 page_range=page_range, page=page)
