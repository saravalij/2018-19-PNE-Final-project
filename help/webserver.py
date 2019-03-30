
from P1.Seq import Seq
import http.server
import socketserver
import termcolor

PORT = 8001


def read_contents(page):
    with open('{}.html'.format(page), 'r') as html_file:
        contents = html_file.read()
    return contents


def command_processing(obj, com, let):
    try:
        if com == 'percentage':
            return str(obj.perc(let))
        elif com == 'count':
            return str(obj.count(let))
    except IndexError:
        return 'Error'


class TestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        """This method is called whenever the client invokes the GET method
        in the HTTP protocol request"""

        termcolor.cprint(self.requestline, 'green')
        termcolor.cprint(self.path, 'blue')

        if self.path == '/':
            contents = read_contents("form")

        elif 'msg' in self.path:
            message = self.path[self.path.index('=')+1:self.path.index('&')]

            # Checking whether it's a valid sequence
            if all(x in ['A', 'C', 'T', 'G'] for x in message.upper()) and message != '':

                results = []
                seq = Seq(message.upper())
                results.append('Introduced sequence: {}'.format(seq.strbase))
                requests = self.path[self.path.index('&')+1:].split('&')
                letter = 'z'

                for r in requests:
                    if 'chk=on' in r:
                        length = seq.len()
                        results.append('Total length: {}'.format(length))
                    elif 'base' in r:
                        letter = r[-1]
                    elif 'operation' in r:
                        if letter != 'z':
                            op = r.partition('=')[2]
                            counting = command_processing(seq, op, letter)
                            results.append('Operation {} on the {} base: {}'.format(op, letter, counting))

                results = '<br>'.join(results)

            else:
                results = 'Sorry, this sequence does not exist.\n'

            contents = read_contents('result').format(results)

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
