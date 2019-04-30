
from Seq import Seq
import http.server
import http.client
import socketserver
import termcolor
import json
import operator


def read_contents(page):
    with open('{}.html'.format(page), 'r') as html_file:
        contents = html_file.read()
    return contents


def get_json(ENDPOINT):

    conn = http.client.HTTPSConnection("rest.ensembl.org")

    additional = '?content-type=application/json'

    if 'overlap' in ENDPOINT:

        additional = additional + ';feature=gene;feature=transcript;feature=cds;feature=exon'

    conn.request('GET', ENDPOINT + additional, None, {'User-Agent': 'http-client'})

    r1 = conn.getresponse()

    text_json = r1.read().decode("utf-8")
    conn.close()

    return json.loads(text_json)


def check_gene(gene):

    xrefs = get_json('/xrefs/symbol/human/{}'.format(gene))

    if len(xrefs) == 0:

        wrong = 'Error. The introduced gene does not exist.'

    elif len(xrefs) > 1:
        ids = []
        genes = []

        for i in xrefs:
            ids.append(i['id'])

        for i in ids:
            if 'display_name' in get_json('/lookup/id/{}'.format(i)):
                genes.append(get_json('/lookup/id/{}'.format(i))['display_name'])

        wrong = 'Error. Maybe you meant any of the next genes: {} ...? Try again.'.format(', '.join(genes))

    else:
        return xrefs[0]['id']

    return wrong


def get_sequence(gene_id):               # maybe unnecessary????

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

        if self.path == '/':
            contents = read_contents("main")

        elif '/listSpecies' in self.path:

            limit = self.path[self.path.index('=')+1:]
            results = []

            if limit.isdigit() is True or limit == '':          # CHECK BC I HAVE CHANGED TO IS TRUE INSTEAD OF == TRUE

                c_names = []

                species = get_json('/info/species')['species']
                species.sort(key=operator.itemgetter('common_name'))

                if limit != '' and limit != '0':

                    if 0 < int(limit) <= len(species):

                        for i in range(int(limit)):
                            c_names.append(species[i]['common_name'].capitalize())

                        for cn in enumerate(c_names, start=1):
                            results.append('. '.join(map(str, cn)) + '<br>')

                        results = ''.join(results)

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

            else:
                results = 'Sorry, that is not a valid limit.'

            contents = read_contents('output').format(results)

        elif '/karyotype' in self.path:

            inspe = self.path[self.path.index('=')+1:]

            if inspe != '':

                if '+' in inspe:
                    inspe = inspe.replace('+', '%20')

                data = get_json('/info/assembly/{}'.format(inspe))
                results = ['']

                if 'error' not in data:
                    for c in data['karyotype']:
                        results.append(c)

                    results = '\n<br>- '.join(results)

                    if len(results) < 1:
                        results = 'Our database does not have a karyotype associated to that species.'
                else:
                    results = 'Oops! We cannot find that species in our database.'

            else:
                results = 'In order to retrieve a karyotype, you must tell us which species you want it of.'

            contents = read_contents('output').format(results)

        elif '/chromosomeLength' in self.path:

            inspe = self.path[self.path.index('=')+1:self.path.index('&')]
            inchromo = self.path[self.path.index('&')+1:]
            inchromo = inchromo[inchromo.index('=')+1:]

            if inspe != '' and inchromo != '':

                data = get_json('/info/assembly/{}/{}'.format(inspe, inchromo))

                if 'error' not in data:
                    results = 'The length of chromosome "{}" of species "{}" is ' \
                              '{}.'.format(inchromo, inspe.capitalize(), data['length'])
                else:
                    results = 'Oops! Error. {}.'.format(data['error'])

            else:
                results = "In order to retrieve any chromosome's length, you must tell " \
                          "us what chromosome of, and to which species it belongs."

            contents = read_contents('output').format(results)

        # Medium level:

        elif '/geneSeq' in self.path:        # very very very long sequence. how to adjust??????

            gene = self.path[self.path.index('=') + 1:]

            gene_id = check_gene(gene)

            if 'Error' not in gene_id:

                results = '''Gene {}\'s sequence is:<br><br>{}.
                '''.format(get_json('/lookup/id/{}'.format(gene_id))['display_name'], get_sequence(gene_id))

            else:
                results = gene_id

            contents = read_contents('output').format(results)

        elif '/geneInfo' in self.path:

            gene_id = check_gene(self.path[self.path.index('=') + 1:])

            if 'Error' not in gene_id:

                info = get_json('/lookup/id/{}'.format(gene_id))

                results = '''Gene {}:<br><br>
                    -ID: {}<br>
                    -In chromosome: {}<br>
                    -Start: {}<br>
                    -End: {}<br>
                    -Length: {}<br>
                    '''.format(info['display_name'], info['id'], info['seq_region_name'],
                               info['start'], info['end'], len(get_sequence(gene_id)))

            else:
                results = gene_id

            contents = read_contents('output').format(results)

        elif '/geneCal' in self.path:

            gene_id = check_gene(self.path[self.path.index('=') + 1:])

            if 'Error' not in gene_id:

                gene_seq = Seq(get_sequence(gene_id))

                results = '''Gene {}:<br><br>
                    -Total length: {}<br>
                    -Percentage of its bases:<br>
                        -A: {}%<br>
                        -C: {}%<br>
                        -G: {}%<br>
                        -T: {}%'''.format(get_json('/lookup/id/{}'.format(gene_id))['display_name'],
                                          gene_seq.len(), gene_seq.perc('A'), gene_seq.perc('C'),
                                          gene_seq.perc('G'), gene_seq.perc('T'))
            else:
                results = gene_id

            contents = read_contents('output').format(results)

        elif '/geneList' in self.path:        # many subgenes of the same gene. delete them????

            path = self.path.partition('&start=')
            region = path[0][path[0].index('=') + 1:]
            start = path[2][:path[2].index('&')]
            end = path[2][path[2].index('=') + 1:]

            ch_locat = get_json('/overlap/region/human/{}:{}-{}'.format(region, start, end))

            if 'error' in ch_locat:
                results = ch_locat['error'] + '. Please, try again.'

            elif len(ch_locat) == 0:
                results = '''There are no genes located in chromosome {} from positions {} to {}.
                '''.format(region.upper(), start, end)

            else:
                genes = []
                for l in ch_locat:
                    if 'external_name' in l:
                        genes.append(l['external_name'])

                results = '''The genes located in chromosome {}, from positions {} to {} are:<br><br>
                    - {}'''.format(region, start, end, '<br>- '.join(genes))

            contents = read_contents('output').format(results)

        else:
            contents = read_contents('error')

        # Generating the response message
        self.send_response(200)  # -- Status line: OK!

        # Define the content-type header:
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(str.encode(contents)))

        # The header is finished
        self.end_headers()

        # Send the body of the response message
        self.wfile.write(str.encode(contents))

        return


# ------------------------
# - Server MAIN program
# ------------------------
# -- Set the new handler
Handler = TestHandler

# -- Open the socket server
with socketserver.TCPServer(("", PORT), Handler) as httpd:

    print("Serving at PORT", PORT)

    # -- Main loop: Attend the client. Whenever there is a new
    # -- clint, the handler is called
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Stoped by the user")
        httpd.server_close()

print("")
print("Server Stopped")
