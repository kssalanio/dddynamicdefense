#!/usr/bin/env python
#  -*-coding:UTF-8 -*

"""
 

 Original code from: https://code.activestate.com/recipes/577260-multi-threaded-smtp-proxy/
 https://github.com/ActiveState/code/tree/master/recipes/Python/577260_Multi_threaded_SMTP_proxy
 Modified by Ken Salanio
"""

#import smtpd, smtplib, asyncore
from __future__ import print_function
import re, sys, os, socket, threading, signal
from select import select
import pdb
import logging, docprocessor
import ConfigParser
from pprint import pprint

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/tmp/content-filter.log',
                    filemode='a')


CRLF="\r\n"
EX_TEMPFAIL = 75
EX_UNAVAILABLE = 69

class SMTPFilterRelayServer:
    """
    An After Queue Relay Server PII Filter for SMTP emails
    """
    def __init__(self, listen_addr, remote_addr, smtp_filter):
        self.local_addr = listen_addr
        self.remote_addr = remote_addr
        self.srv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.srv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv_socket.bind(listen_addr)
        self.smtp_filter = smtp_filter

        self.please_die = False

        self.accepted = {}

    def start(self):
        """
        Main start function
        """
        #self.start_blocking()
        self.start_nonblocking()

    def start_nonblocking(self):
        """
        Non blocking start function
        """
        self.srv_socket.setblocking(0)
        self.srv_socket.listen(5)
        print("Started non-blocking socket. Listening on "+str(self.local_addr))

        while not self.please_die:

            try:
                ready_to_read, ready_to_write, in_error = select([self.srv_socket], [], [], 0.1)
            except Exception as err:
                print("ERROR: %s" % err.message)
                pass

            #print("Socket status: "+ str((ready_to_read, ready_to_write, in_error)))
            if len(ready_to_read) > 0:
                try:
                    print("Waiting for a connection @ [%s]..." % str(self.local_addr))
                    client_socket, client_addr = self.srv_socket.accept()
                except Exception as err:
                    print("Problem:", err)
                else:
                    print("Connection from {0}:{1}".format(client_addr[0], client_addr[1]))
                    tclient = ThreadClient(self, client_socket, self.remote_addr)
                    tclient.start()
                    self.accepted[tclient.getName()] = tclient

    def start_blocking(self):
        """
        Blocking start function
        """
        self.srv_socket.listen(5)
        print("Started blocking socket. Listening on " + str(self.local_addr))

        while not self.please_die:
            try:
                print("Waiting for a connection @ [%s]..." % str(self.local_addr))
                client_socket, client_addr = self.srv_socket.accept()
            except Exception as err:
                print("Problem:", err)
            else:
                print("Connection from {0}:{1}".format(client_addr[0], client_addr[1]))
                tclient = ThreadClient(self, client_socket, self.remote_addr)
                tclient.start()
                self.accepted[tclient.getName()] = tclient


    def die(self):
        """Used to kill the server (joining threads, etc...)
        """
        print("Killing all client threads...")
        self.please_die = True
        for tc in self.accepted.values():
            tc.die()
            tc.join()

class ThreadClient(threading.Thread):
    """This class is used to manage a 'client to final SMTP server' connection.
    It is the 'Proxy' part of the program
    """
    (MAIL_DIALOG, MSG_HEADER, MSG_BODY) = range(3)
    def __init__(self, serv, conn, remote_addr):
        threading.Thread.__init__(self)
        self.server = serv
        self.local = conn
        self.remote_addr = remote_addr
        self.remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.please_die = False
        self.mbuffer = []
        self.msg_state = ThreadClient.MAIL_DIALOG

    def recv_body_line(self, line):
        """Each line of the body is received here and can be processed, one by one.
        A typical behaviour should be to send it immediately... or keep all the
        body until it reaches the end of it, and then process it and finally,
        send it.

        Body example:
            Hello foo !
            blabla
        """
        mline = "{0}{1}".format(line, CRLF)
        print("B>", line)
        self.mbuffer.append(line)

    def flush_body(self):
        """This method is called when the end of body (matched with a single
        dot (.) on en empty line is encountered. This method is useful if you
        want to process the whole body.
        """
        #filter_result = self.server.smtp_filter.redact_smtp(self.mbuffer)
        filter_result = self.server.smtp_filter.redact_smtp_test(self.mbuffer)

        # NOTE: Original flush send
        for line in filter_result:

            mline = "{0}{1}".format(line, CRLF)
            print("~B>", mline)
            self.remote.send(mline.encode())

        # NOTE: New flush send

        # Append example:
        #toto = "---{0}{0}Un peu de pub{0}".format(CRLF)
        #self.remote.send(toto.encode())

    def recv_header_line(self, line):
        """All header lines (subject, date, mailer, ...) are processed here.
        """
        mline = "{0}{1}".format(line, CRLF)
        print("H>", line)
        self.remote.send(mline.encode())

    def recv_server_dialog_line(self, line):
        """All 'dialog' lines (which are mail commands send by the mail client
        to the MTA) are processed here.

        Dialog example:
            MAIL FROM: foo@bar.tld
        """
        mline = "{0}{1}".format(line, CRLF)
        print(">>", line)
        self.remote.send(mline.encode())

    def run(self):
        """Here is the core of the proxy side of this script:
        For each line sent by the Mail client to the MTA, split it on the CRLF
        character, and then:
            If it is a DOT on an empty line, call the 'flush_body()' method
            else, if it matches 'DATA' begin to process the body of the message,
            else:
                if we're processing the header, give each line to the
                   'recv_header_line()' method,
                else if we're processing the 'MAIL DIALOG' give the line to the
                     'recv_server_dialog_line()' method.
                else, consider that we're processing the body and give each line
                      to the 'recv_body_line()' method,
        """
        self.remote.connect(self.remote_addr)
        self.remote.setblocking(0)
        while not self.please_die:
            # Check if the client side has something to say:
            ready_to_read, ready_to_write, in_error = select([self.local], [], [], 0.1)
            if len(ready_to_read) > 0:
                try:
                    msg = self.local.recv(1024)
                except Exception as err:
                    print(str(self.getName()) + " > " + str(err))
                    break
                else:
                    dmsg = msg.decode()
                    if dmsg != "":
                        dmsg = dmsg.strip(CRLF)
                        for line in dmsg.split(CRLF):
                            mline = "{0}{1}".format(line,CRLF)
                            if line != "":
                                if line == "DATA":
                                    # the 'DATA' string means: 'BEGINNING of the # MESSAGE { HEADER + BODY }
                                    self.msg_state = ThreadClient.MSG_HEADER
                                    self.remote.send(mline.encode())
                                elif line == ".":
                                    # a single dot means 'END OF MESSAGE { HEADER+BODY }'
                                    self.msg_state = ThreadClient.MAIL_DIALOG
                                    self.flush_body()
                                    self.remote.send(mline.encode())
                                else:
                                    # else, the line can be anything and its
                                    # signification depend on the part of the
                                    # whole dialog we're processing.
                                    if self.msg_state == ThreadClient.MSG_HEADER:
                                        self.recv_header_line(line)
                                    elif self.msg_state == ThreadClient.MAIL_DIALOG:
                                        self.recv_server_dialog_line(line)
                                    else:
                                        self.recv_body_line(line)
                            else:
                                # Probably the most important: An empty line
                                # inside the { HEADER + BODY } part of the
                                # message means we're done with the 'HEADER'
                                # part and we're beginning the BODY part.
                                self.msg_state = ThreadClient.MSG_BODY
                    else:
                        break

            # Check if the server side has something to say:
            ready_to_read, ready_to_write, in_error = select([self.remote], [], [], 0.1)
            if len(ready_to_read) > 0:
                try:
                    msg = self.remote.recv(1024)
                except Exception as err:
                    print(str(self.getName()) + " > " + str(err))
                    break
                else:
                    dmsg = msg.decode()
                    if dmsg != "":
                        print("<< {0}".format(repr(msg.decode())))
                        self.local.send(dmsg.encode())
                    else:
                        break

        self.remote.close()
        self.local.close()
        self.server.accepted.pop(self.getName())

    def die(self):
        self.please_die = True

if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('config.ini')

    smtp_filter = docprocessor.DocumentProcessor(config)

    #srv = Server(("127.0.0.1", 10025), ("127.0.0.1", 10026))
    smtp_filter_relay = SMTPFilterRelayServer(("0.0.0.0", 10025), ("127.0.0.1", 10026), smtp_filter)
    def die(signum, frame):
        global smtp_filter_relay
        smtp_filter_relay.die()

    signal.signal(signal.SIGINT, die)
    signal.signal(signal.SIGTERM, die)

    smtp_filter_relay.start()


