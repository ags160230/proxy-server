#!/usr/bin/env python

from socket import *
import sys, os, thread, socket

# Establish maximum number of connections
max_conns = 5

# Establish maximum buffer size (4096 is recommended)
buffer_size = 4096

# Server IP address
host = "0.0.0.0"

# Server port number
port = 12345

################################################################################
#                                                                              #
#           Function to initialize the server end of the web proxy,            #
#           binding the listening socket to IP address 0.0.0.0 and             #
#           port number 12345,                                                 #
#                                                                              #
################################################################################
def initialize():
    try:
        print "WELCOME TO THE WEB PROXY!\n"

        # Create the server socket
        # ss = serverSocket
        ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to respective IP address and port number
        ss.bind((host, port))
        print "Socket binded to port: %s" % (port)

        # Put the socket into listening mode
        ss.listen(max_conns)
        print "Socket is listening..."
        print "--------------------------------------------------------------------"

        # Start receiving data from the client
        while True:

            print "Ready to serve...\n"

            # Create client socket upon successful connection
            # cs = clientSocket
            cs, addr = ss.accept()

            print "Received a connection from: ", addr

            # Start new thread that invokes proxy_thread()
            thread.start_new_thread(proxy_thread, (cs, addr))

        ss.close()

    # Exception handler for socket initiation failure
    except Exception:
        if ss:
            ss.close()

        print "Unable to initialize socket!"
        sys.exit(1)

    # Exception handler for user entering (ctrl + c)
    except KeyboardInterrupt:
        print "\nUser requested an interrupt!"
        print "Exiting..."
        ss.close()
        sys.exit(1)

################################################################################
#                                                                              #
#         Function to handle GET requests send from the client socket,         #
#         which parses the request and searches for an instance of the         #
#         request in a cache directory                                         #
#                                                                              #
################################################################################

def proxy_thread(cs, addr):

    # Recieve GET request on client socket
    request = cs.recv(buffer_size)

    # Condition to filter out non-GET requests in the browser traffic
    if "GET" not in request:
        print "Ignore Request (NOT GET)..."
        print "--------------------------------------------------------------------"
        sys.exit(1)
    else:
        print "Request accepted (GET)!"
        print "--------------------------------------------------------------------"


    # Print here for testing
    print "################ Begin parsing of the GET request ##################"
    print "REQUEST:\n" + request
    print "--------------------------------------------------------------------"

#------------------- Begin parsing of the GET request -------------------------#

    first_line = request.splitlines()[0]

    # Print here for testing
    print "REQ: " + first_line
    print "--------------------------------------------------------------------"

    url = first_line.split(" ")[1]

    # Print here for testing
    print "URL: " + url
    print "--------------------------------------------------------------------"

    http_pos = url.find("://")

    if (http_pos == -1):
        temp = url
    else:
        temp = url[(http_pos + 3):]

    # Print here for testing
    print "TEMP: " + temp
    print "--------------------------------------------------------------------"

    port_pos = temp.find(":")

    web_server_pos = temp.find("/")

    if (web_server_pos == -1):
        web_server_pos = len(temp)

    web_server = ""

    port = -1

    if(port_pos == -1 or web_server_pos < port_pos):
        port = 80
        web_server = temp[:web_server_pos]
    else:
        port = int((temp[(port_pos + 1):])[:web_server_pos - port_pos - 1])
        web_server = temp[:port_pos]

    # Print here for testing
    print "port number: " + str(port)
    print "--------------------------------------------------------------------"
    print "web server: " + web_server

    print "################# End parsing of the GET request ###################\n"

#--------------------- End parsing of the GET request -------------------------#

#--------------------------- Begin search of Cache ----------------------------#

    cached_file = False

    try:
        print "################### Begin search of cache ######################"
        print "Searching cache..."

        (filepath, filename) = os.path.split(url)

        # Print here for testing
        print "FILENAME: " + filename
        print "--------------------------------------------------------------------"
        print "FILEPATH: " + filepath
        print "--------------------------------------------------------------------"

        if filename is "":
            path = filepath.lstrip("https://") + "/index.html"
        else:
            path = filepath.lstrip("https://") + "/" + filename

        # Print here for testing
        print "Searched PATH: " + path

        f = open("http:/" + path, "r")

        output_data = f.readlines()

        for i in range(0, len(output_data)):

            #print "OUTPUT_DATA[" + str(i) + "]:\n"
            #temp = unicode(output_data[i], errors = "ignore")
            #print temp.encode("utf-8")
            #print type(temp)
            #print "--------------------------------------------------------------------"

            #cs.send(output_data[i].decode("latin1"))
            #cs.send(temp.encode("utf-8"))
            cs.send(output_data[i])

        print "Read from cache!"

        cached_file = True

        # cs.send("HTTP/1.0 200 OK\r\n")
        cs.send("HTTP/1.1 200 OK\r\n")
        cs.send("Content-Type:text/html\r\n")

        f.close()
        cs.close()

        print "#################### End search of cache #######################\n"
#---------------------------- End search of Cache -----------------------------#

    # Exception handler to catch IO error signaling that there was no cache hit
    # This in turn will call forward_request() to forward the GET request to the
    #   webserver
    except IOError:
        if cached_file == False:
            forward_request(cs, addr, web_server, port, url, request)

################################################################################

def forward_request(cs, addr, web_server, port, url, request):
    try:
        print "\n############### Begin forwarding of the request #################"
        print "Forwarding the request..."

        print "--------------------------------------------------------------------"
        print "FORWARDED REQUEST:\n"
        print "--------------------------------------------------------------------"

        # Create a "proxy" socket for the proxied GET request to the appopriate
        #   webserver
        # ps = proxySocket
        ps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ps.connect((web_server, port))
        #ps.send(request)
        ps.sendall(request)

        while 1:

            # Print here for testing
            print "test 1"

            data = ps.recv(buffer_size)

            # Error handling for the event that a 404 message is returned for
            #   the requested web page
            if "404 Not Found" in data:
                cs.send("HTTP/1.1 404 Not Found\r\n")
                sys.exit(1)

            # Print here for testing
            print "RETURN DATA:\n" + data
            print "--------------------------------------------------------------------"

            if(len(data) > 0):

                # Print here for testing
                print "test 2"

                cs.send(data)

                (filepath, filename) = os.path.split(url)

                # Print here for testing
                print "(CS) FILEPATH: " + filepath
                print "--------------------------------------------------------------------"
                print "(CS) FILENAME: " + filename
                print "--------------------------------------------------------------------"

                http_pos = url.find("://")

                if (http_pos == -1):
                    path = url
                else:
                    path = url[(http_pos + 3):]

                try:
                    # Print here for testing
                    print "test 3"

                    if not os.path.exists(filepath):
                        os.makedirs(filepath)

                    # Print here for testing
                    print "test 4"

                    if (filename == ""):
                        path = filepath + "/index.html"
                    else:
                        path = filepath + "/" + filename

                    # Print here for testing
                    print "(CS) PATH: " + path
                    print "--------------------------------------------------------------------"

                    f = open(path, "a")

                    f.write(data)
                    f.close()

                except IOError:
                    print "Could not open directory!"
                    break
            else:
                break

            ps.close()
            cs.close()

    except socket.error as error_msg:
        print "ERROR: ", addr, error_msg

        if cs:
            print "Client Socket closed: Error occured!"
            cs.close()
        if ps:
            print "Proxy Socket closed: Error occured!"
            ps.close()

        print "################ End forwarding of the request ##################\n"

        sys.exit(1)

################################################################################

# Call initialize() to begin program
initialize()
