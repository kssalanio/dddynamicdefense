from flask import send_file
from flask import Flask
from flask import request

import cv2
import numpy as np
import urllib
import io
from gcp_imageredaction import redact_image_fileinmemory
from gcp_imageredaction import redact_image_fileondisk

from StringIO import StringIO
from zipfile import ZipFile
from urllib import urlopen
import zipfile
from os.path import basename
import hashlib
import os

from werkzeug.serving import WSGIRequestHandler
WSGIRequestHandler.protocol_version = "HTTP/1.1"

app = Flask(__name__)
@app.route('/redactimage')
def doredactimage():
    url = request.args.get('url', '')
    print("intercepted",url)

    resp = urllib.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    img = cv2.imdecode(image, 1)

    if '.jpg' in url:
        ft='jpg'
        imgtosend=cv2.imencode(".jpg", img)[1].tostring()

    elif '.png' in url:
        ft='png'
        imgtosend=cv2.imencode(".png", img)[1].tostring()

    redactedimage=redact_image_fileinmemory(project='<GCP project name>', filetype=ft,
                                         image_binary=imgtosend,
                                         info_types=['DATE','LOCATION','PERSON_NAME','PHONE_NUMBER','CREDIT_CARD_NUMBER'],
                                         min_likelihood='POSSIBLE')

    if '.jpg' in url:
        return send_file(io.BytesIO(redactedimage), mimetype='image/jpeg')
    elif '.png' in url:
        return send_file(io.BytesIO(redactedimage), mimetype='image/png')

@app.route('/redactzip')
def doredactzip():
    url = request.args.get('url', '')
    print("intercepted",url)

    origzipfilename = url.rsplit('/', 1)[1]                 #get original zip file name
    origzipfilename = origzipfilename.split('.zip', 1)[0]   #cont.

    resp = urlopen(str(url))
    zf = ZipFile(StringIO(resp.read()))                     #get zip file
    zflist=zf.namelist()                                    #zflist is list of files in zip file
    if (any(".jpg" in s for s in zflist) or (".png" in s for s in zflist)): #if jpg or png file in zip
        m = hashlib.md5()
        m.update(url)                                       #get md5sum of zipfile url
        tmpdir='/tmp/{}'.format(str(m.hexdigest()))
        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)                                #make dir in /tmp/<md5sum>
            os.mkdir('{}/redacted'.format(tmpdir))
        zf.extractall(tmpdir)                               #extract zip to tmpdir
        forwriting=[]                                       #fill this list with paths to redacted image
        for filein in zf.namelist():
            if ('.jpg' in filein) or ('.png' in filein):
                filename='{}/{}'.format(tmpdir,filein)
                output_filename = redact_image_fileondisk(project='<GCP project name>', filename=filename,
                                               output_filename='{}/redacted/{}'.format(tmpdir,filein),
                                               info_types=['DATE', 'LOCATION', 'PERSON_NAME', 'PHONE_NUMBER',
                                                           'CREDIT_CARD_NUMBER'],
                                               min_likelihood='POSSIBLE')
                forwriting.append(output_filename)
            else:
                forwriting.append('{}/{}'.format(tmpdir,filein))

        memory_file = io.BytesIO()
        with ZipFile(memory_file, 'w') as zf:
            for tozipfile in forwriting:
                zf.write(tozipfile,
                     basename(tozipfile))
        memory_file.seek(0)
        return send_file(memory_file, attachment_filename="{}.zip".format(origzipfilename), as_attachment=True)
    else:
        return send_file(zf, attachment_filename="{}.zip".format(origzipfilename), as_attachment=True)
