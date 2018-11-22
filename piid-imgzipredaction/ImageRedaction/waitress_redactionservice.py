from waitress import serve
import webapp_redactionservice
serve(webapp_redactionservice.app, host='0.0.0.0', port=5000)