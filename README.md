# PresentationTimer
This repo contains a presentation timer overlay with a progress bar. The timer can be controlled (start/stop, reset) by a small web server.
I use this in some of my seminars. 

## Start timer
python3 timerbar.py --duration-minutes 10 --server-url <server_URL> --auth-token <token> --ca-cert cert.pem

## Start server
python3 server.py --auth-token <token> --host 0.0.0.0 --port 5000 --cert cert.pem --key key.pem

## Access conroll page
https://<server_URL>/?token=<token>

## Warning!
Security is vibe coded. It should just make it harder for seminar participants to interfere. 