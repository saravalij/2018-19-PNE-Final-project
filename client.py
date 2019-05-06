import http.client
import json

# Client to test the advanced level of the practice (even though it can also
# send output corresponding to the other levels)

SERVER = 'localhost'
PORT = 8000
METHOD = "GET"
headers = {'User-Agent': 'http-client'}

arguments = ['/listSpecies?limit=23&json=1', '/karyotype?json=1&specie=human', '/chromosomeLength?json=1',
             '/geneSeq?gene=starsss&json=1', '/geneCalc?json=1&gene=frat1', '/geneInfo?gene=ecop&json=1',
             '/geneList?json=1&end=123456&chromo=7&start=789', '/10json=1']

try:
    for ENDPOINT in arguments:
        conn = http.client.HTTPConnection(SERVER, PORT)

        conn.request(METHOD, ENDPOINT, None, headers)

        r1 = conn.getresponse()

        print()

        if 'json=1' in ENDPOINT:
            text_json = r1.read().decode("utf-8")
            data = json.loads(text_json)

        else:
            # if we were to try paths that did not include "json=1", the html file would be printed on the console,
            # but since this client's goals is tot est whether jsons are produced, this part is not implemented.

            data = r1.read().decode('utf-8')

        print()
        print(data)

        conn.close()

except KeyboardInterrupt:
    print('\n\n---> Program stopped by the user.')
