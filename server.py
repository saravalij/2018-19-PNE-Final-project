
from Seq import Seq
import http.server
import http.client
import socketserver
import termcolor
import json
import operator
import string


socketserver.TCPServer.allow_reuse_address = True


def read_contents(page):   # Function that opens and reads html files

    with open('{}.html'.format(page), 'r') as html_file:
        contents = html_file.read()
    return contents


def get_parameters(path):   # Function that returns dictionaries with the parameters passed as arguments

    if '?' in path:
        if '=' in path:
            if '&' in path:

                path = path[path.index('?')+1:].split('&')
                keys = []
                values = []
                for p in path:
                    p = p.split('=')
                    keys.append(p[0])
                    values.append(p[1])
                return dict(zip(keys, values))
            else:
                return {path[path.index('?')+1:path.index('=')]: path[path.index('=')+1:]}

        else:
            return {'error': 'incorrect endpoint calling'}
    else:
        return {'error': 'incorrect endpoint calling'}


def get_json(ENDPOINT):    # Function that access information contained in json files on the Ensembl API

    conn = http.client.HTTPSConnection("rest.ensembl.org")

    additional = '?content-type=application/json'

    if 'overlap' in ENDPOINT:

        additional = additional + ';feature=gene'

    conn.request('GET', ENDPOINT + additional, None, {'User-Agent': 'http-client'})

    r1 = conn.getresponse()

    text_json = r1.read().decode("utf-8")
    conn.close()

    return json.loads(text_json)


def check_gene(gene):      # Function that checks whether a gen exists or is valid.

    for x in gene:
        if x in string.punctuation:     # Some genes have . or - as part of their name
            if x != '.' and x != '-':
                gene = 0
                break

    xrefs = get_json('/xrefs/symbol/human/{}'.format(gene))

    if len(xrefs) == 0 or gene.isdigit() is True:

        return 'Error. The introduced gene does not exist.'

    else:
        # In cases where there's more than one entry for the introduced gene, we'll take just
        # the first one and work with it.
        return xrefs[0]['id']


def get_sequence(gene_id):     # Function that returns the sequence of a given gene, using its id

    seq = get_json('/sequence/id/{}'.format(gene_id))['seq']

    return seq


PORT = 8000
socketserver.TCPServer.allow_reuse_address = True


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        """This method is called whenever the client invokes the GET method
        in the HTTP protocol request"""

        termcolor.cprint(self.requestline, 'green')
        termcolor.cprint(self.path, 'blue')

        # Basic level:

        res_dict = 'n'  # If the arguments passed produce valid outputs, this variable will be renamed and
        # used to retrieve and print different information

        title = 'to_be_determined'  # So no warning appears in PyCharm

        if self.path == '/':
            results = 'main'

        elif '/listSpecies' in self.path:

            title = 'List Species'
            results = []

            if 'limit' not in self.path:
                limit = '0'
            else:
                if '=' not in self.path:
                    # Word limit appears in the path but has no '=' that can be followed by a value
                    limit = 'incorrect'
                else:
                    limit = get_parameters(self.path)['limit']

            if limit.isdigit() is True or limit == '':

                c_names = []

                species = get_json('/info/species')['species']
                species.sort(key=operator.itemgetter('common_name'))    # This way, species will be in order always

                if limit != '' and limit != '0':

                    if 0 < int(limit) <= len(species):

                        for i in range(int(limit)):
                            c_names.append(species[i]['common_name'].capitalize())

                        for cn in enumerate(c_names, start=1):
                            results.append('. '.join(map(str, cn)) + '<br>')   # Printing it nicely

                        results = ''.join(results)
                        res_dict = dict(zip(list(range(1, int(limit) + 1)), c_names))    # Part of the advanced level

                    elif int(limit) < 0:
                        results = 'Sorry, that is not a valid limit'

                    elif int(limit) >= len(species):
                        results = 'That limit is outrange because there are not so many species.'

                else:
                    for n in species:
                        c_names.append(n['common_name'].capitalize())

                    for cn in enumerate(c_names, start=1):

                        results.append('. '.join(map(str, cn)) + '<br>')

                    results = ''.join(results)
                    res_dict = dict(zip(list(range(1, len(c_names) + 1)), c_names))

            else:
                results = 'Sorry, that is not a valid limit.'

        elif '/karyotype' in self.path:

            expected = ['specie', 'json']
            inspe = get_parameters(self.path)

            if len(inspe.keys()) == 1 and 'json' in inspe.keys():
                # In case the only parameter passed is "json", an error message must appear
                results = '0'

            elif all(x in expected for x in inspe.keys()) is True and all(x != '' for x in inspe.values()) is True:
                # Checking whether all parameters passed are the ones that should be passed and also that all these
                # parameters have an associated value
                inspe = inspe['specie']
                title = '{} karyotype'.format(inspe.capitalize())

                if inspe != '':

                    if '+' in inspe:   # For species whose name is formed by two words
                        inspe = inspe.replace('+', '%20')

                    data = get_json('/info/assembly/{}'.format(inspe))
                    results = ['']
                    karyo = []

                    if 'error' not in data:
                        for c in data['karyotype']:
                            results.append(c)
                            karyo.append(c)

                        results = '<br>&#8259;    '.join(results)
                        res_dict = dict(zip(list(range(1, len(karyo)+1)), karyo))

                        if len(results) < 1:
                            results = 'Our database does not have a karyotype associated to that species.'
                    else:
                        results = 'Oops! We cannot find that species in our database.'

                else:
                    results = 'In order to retrieve a karyotype, you must tell us which species you want it of.'

            else:
                results = '0'

        elif '/chromosomeLength' in self.path:

            expected = ['specie', 'chromo', 'json']
            param = get_parameters(self.path)

            if len(param.keys()) == 1 and 'json' in param.keys():
                results = '0'

            elif all(x in expected for x in param.keys()) is True and all(x != '' for x in param.values()) is True:

                title = 'Chromosome Length'
                inspe = param['specie']
                inchromo = param['chromo']

                data = get_json('/info/assembly/{}/{}'.format(inspe, inchromo))

                if 'error' not in data:
                    results = 'The length of chromosome "{}" of species "{}" is ' \
                                  '{}.'.format(inchromo.capitalize(), inspe.capitalize(), data['length'])
                    res_dict = {'length of chromosome': data['length']}
                else:
                    results = 'Oops! Error. {}.'.format(data['error'])

            else:
                results = '0'

        # Medium level:

        elif '/geneSeq' in self.path:

            expected = ['gene', 'json']
            gene = get_parameters(self.path)

            if len(gene.keys()) == 1 and 'json' in gene.keys():
                results = '0'

            elif all(x in expected for x in gene.keys()) is True and all(x != '' for x in gene.values()) is True:
                title = 'Gene Sequence'
                gene = gene['gene']

                gene_id = check_gene(gene)

                if 'Error' not in gene_id:

                    results = get_sequence(gene_id)

                    title = 'Gene {} Sequence'.format(get_json('/lookup/id/{}'.format(gene_id))['display_name'])
                    res_dict = {'gene sequence': results}

                else:
                    results = gene_id
            else:
                results = '0'

        elif '/geneInfo' in self.path:

            expected = ['gene', 'json']
            gene = get_parameters(self.path)

            if len(gene.keys()) == 1 and 'json' in gene.keys():
                results = '0'

            elif all(x in expected for x in gene.keys()) is True and all(x != '' for x in gene.values()) is True:

                title = 'Gene Info'
                gene_id = check_gene(gene['gene'])

                if 'Error' not in gene_id:

                    info = get_json('/lookup/id/{}'.format(gene_id))

                    results = '''
                        -  ID: {}<br>
                        -  In chromosome: {}<br>
                        -  Start: {}<br>
                        -  End: {}<br>
                        -  Length: {}<br>
                        '''.format(info['id'], info['seq_region_name'], info['start'],
                                   info['end'], len(get_sequence(gene_id)))

                    title = 'Gene {} Info'.format(info['display_name'])
                    res_dict = dict(zip(['id', 'in chromosome', 'start', 'end', 'length'],
                                        [info['id'], info['seq_region_name'], info['start'],
                                         info['end'], len(get_sequence(gene_id))]))

                else:
                    results = gene_id
            else:
                results = '0'

        elif '/geneCalc' in self.path:

            expected = ['gene', 'json']
            gene = get_parameters(self.path)

            if len(gene.keys()) == 1 and 'json' in gene.keys():
                results = '0'

            elif all(x in expected for x in gene.keys()) is True and all(x != '' for x in gene.values()) is True:

                title = 'Gene Calculations'
                gene_id = check_gene(gene['gene'])

                if 'Error' not in gene_id:

                    gene_seq = Seq(get_sequence(gene_id))

                    results = '''
                        -  Total length: {}<br>
                        -  Percentage of its bases:<br>
                        &emsp;-  A: {}%<br>
                        &emsp;-  C: {}%<br>
                        &emsp;-  G: {}%<br>
                        &emsp;-  T: {}%'''.format(gene_seq.len(), gene_seq.perc('A'), gene_seq.perc('C'),
                                                  gene_seq.perc('G'), gene_seq.perc('T'))

                    title = 'Gene {} Calculations'.format(get_json('/lookup/id/{}'.format(gene_id))['display_name'])
                    res_dict = dict(zip(['length', 'bases percentages'],
                                        [gene_seq.len(), dict(zip(['A', 'C', 'G', 'T'],
                                                                  [gene_seq.perc('A'), gene_seq.perc('C'),
                                                                   gene_seq.perc('G'), gene_seq.perc('T')]))]))

                else:
                    results = gene_id
            else:
                results = '0'

        elif '/geneList' in self.path:

            expected = ['chromo', 'start', 'end', 'json']
            param = get_parameters(self.path)

            if len(param.keys()) == 1 and 'json' in param.keys():
                results = '0'

            elif all(x in expected for x in param.keys()) is True and all(x != '' for x in param.values()) is True:

                title = 'Gene List'
                start = param['start']
                end = param['end']
                region = param['chromo']

                ch_locat = get_json('/overlap/region/human/{}:{}-{}'.format(region, start, end))

                if 'error' in ch_locat:
                    if 'maximum allowed' in ch_locat['error']:
                        results = 'Request smaller regions of the sequence. Maximum allowed length: 5000000. Try again.'
                    else:
                        results = ch_locat['error'] + '. Try again.'

                elif len(ch_locat) == 0:
                    results = '''There are no genes located in chromosome "{}" from positions {} to {}.
                    '''.format(region.upper(), start, end)

                else:
                    genes = []
                    for l in ch_locat:
                        if 'external_name' in l:
                            genes.append(l['external_name'])

                    results = '''The genes located in human chromosome "{}", from position {} to position {} are:<br>
                    <br>&emsp;- {}'''.format(region.upper(), start, end, '<br>&emsp;- '.join(genes))

                    res_dict = {'genes': dict(zip(list(range(1, len(genes)+1)), genes))}
            else:
                results = '0'
        else:
            results = 'error'

        # Advanced level:

        if 'json=1' in self.path:    # A json object is be obtained -- ADVANCED

            data = dict()
            if results == '0':     # Wrong endpoint/path calling
                data['error'] = '''Apparently you called an endpoint incorrectly. 
                Maybe you need to double-check the introduced parameters, or introduce some mandatory ones.'''
            elif results == 'error':     # Inexistent endpoint
                data['error'] = 'This page does not exist.'
            else:
                if res_dict != 'n':     # No valid output obtained
                    data['results'] = res_dict
                else:       # Valid output, complete json created
                    data['error'] = results
            contents = json.dumps(data)

        else:    # To be tried on html, and html files to be seen -- BASIC AND MEDIUM

            if results == 'main':
                contents = read_contents('main')
            elif results == '0':
                contents = read_contents('output').format('Oops!', '''Apparently you called an endpoint incorrectly. 
                Maybe you need to double-check the introduced parameters, or introduce some mandatory ones.''')
            elif results == 'error':
                contents = read_contents('error')
            else:
                contents = read_contents('output').format(title, results)

        self.send_response(200)

        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(str.encode(contents)))

        self.end_headers()

        self.wfile.write(str.encode(contents))

        return


# MAIN PROGRAM:
Handler = TestHandler

# Opening the socket server
with socketserver.TCPServer(("", PORT), Handler) as httpd:

    print("Serving at PORT", PORT)

    # Attending the client
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("---> Program stopped by the user")
        httpd.server_close()

print("")
print("Server Stopped")
