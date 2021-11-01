from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections
from tqdm import tqdm

from collectiegroesbeek.spelling import extract_names, generate_word_variants

connections.create_connection('default', hosts=['localhost:9203'])


def main():
    s = Search(index='namenindex')
    s = s.source(fields=['inhoud'])
    s = s.filter('exists', field='inhoud')
    for doc in tqdm(s, total=s.count()):
        names = extract_names(doc.inhoud)
        for name in names:
            for word in name.split():
                variants = generate_word_variants(word.strip(' ;,.'))
                if len(variants) > 1:
                    print(variants)


if __name__ == '__main__':
    main()
