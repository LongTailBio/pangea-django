import entrezpy.esearch.esearcher
import entrezpy.efetch.efetcher

e = entrezpy.esearch.esearcher.Esearcher('esearcher', 'email')
a = e.inquire({'db': 'bioproject', 'term': 'PRJNA545410'})

print(type(a))
print([
    method_name for method_name in dir(a)
    if callable(getattr(a, method_name))]
)

r = a.get_result()
print(type(r))
print(dir(r))
print()
print(r.dump())
print(r.uids)

e = entrezpy.efetch.efetcher.Efetcher('efetcher',
                                      'email',
                                      apikey=None,
                                      apikey_var=None,
                                      threads=None,
                                      qid=None)
analyzer = e.inquire({'db' : 'pubmed',
                      'id' : [545410],
                      'retmode' : 'text',
                      'rettype' : 'abstract'})
print()
print(analyzer)
print(dir(analyzer))


print(analyzer.get_result())