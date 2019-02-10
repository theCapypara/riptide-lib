#### NOTES


"""
API:
TODO: NÖÖÖÖÖÖÖÖ - Erklärung für BA: Wollte gerne NodeJS nehmen aber Probleme mit Cross-Container Kommunikation,
      kann man viel schreiben...
      twistedweb

Anleitung Proxy Server: - https://null-byte.wonderhowto.com/how-to/sploit-make-proxy-server-python-0161232/
                        - https://www.geeksforgeeks.org/creating-a-proxy-webserver-in-python-set-1/

Qullen:
- https://docs.docker.com/network/host/
- Etwas zu Socket Passing
- docker.internal.blub geht nur unter Windows/Mac
- docker0 gibt's nur unter Linux
---> Docker Container kann nicht einfach wieder mit Host reden.

idee war eigentlich (nach diesem api.py blösinn)
TODO: Lieber als Apiserver
Proxy Server läuft im Riptide network und verbindet sich so mit Apiserver und Containern.

"""
