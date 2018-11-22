//
// image-override.js
//      Bettercap caplet that redirects all jpg/png and zip requests to RedactionWebApp with host and path as arguments

function onRequest(req, res) {

    var imgreq_host = req.Hostname
    var imgreq_path = req.Path

    var RedactionWebApp = "192.168.161.165:5000" // redaction web service ip:port


    if (imgreq_path.match(".jpg")
        ||imgreq_path.match(".png")
        ||imgreq_path.match(".JPG")
        ||imgreq_path.match(".PNG"))
    {
       req.Hostname=RedactionWebApp
       req.Path="/redactimage?url=http://" + imgreq_host + imgreq_path
    }

    if (imgreq_path.match(".zip")
        ||imgreq_path.match(".ZIP"))
    {
       req.Hostname=RedactionWebApp
       req.Path="/redactzip?url=http://" + imgreq_host + imgreq_path
    }
}
