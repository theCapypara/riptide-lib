Allgemein:
- Start Check
  - Erreichbar? [Nur mit Port]
  - Wirklich gestartet / Port ist da (falls definiert) / Label sind da? [E]
  - Nur subset
- Stop Check
  - Nicht mehr erreichbar? [Nur ohne Port]
  - Wirklich gestoppt? [E]
  - Nur subset
- cmd_detached
  - Wirklich gestoppt? [E]
- exec
- path_rm
  - Wirklich gestoppt? [E]
- path_copy
  - Wirklich gestoppt? [E]

Services:
- Alle haben Port, es sei denn anders angegeben
- Role main
- Custom Role ("Varnish Test")
- Role src
  - Webserver mit custom sourcen
  - Webserver ohne
  - Permissions im src
  - Volume ist da [E]
- Custom Command
  - Envs sind da [E]
- Pre Start (darf jeweils nichts im container ändern das kein volume ist)
  - Wirklich gestoppt? [E]
- Post Start (darf sachen im container ändern)
- environment variables
  - Direkter Test
  - Envs sind da [E]
- config
  - variablen auswertung
  - berechtigungen
  - Dateien sind da
  - Volumes sind da [E]
- run_as_root
  - Direkter Test
  - Flag korrekt gesetzt [E]
- dont_create_user
  - Direkter Test
  - Flag korrekt gesetzt [E]
- working_directory
  - absolut
  - relativ (nur mit rolle src)
  - relativ ohne rolle src, error handling
  - WD ist da [E]
- additional_ports
  - Auswahl-Logik (ports.json faken)
  - Test erreichbarkeit
  - Test erreichbarkeit auch ohne "port"
  - Ports sind da [E]
- additional_volumes:
  - rw
  - ro
  - rw absolut
  - nicht angegeben
  - Dateien sind da (wenn über _riptide Ordner)
  - Volumes sind da [E]
- Logging (alle via _riptide testen):
  - stdout
  - stderr
  - paths
  - commands
- Connectivity test (zwei Services funken sich an)

Commands:
- Alias
- Alias für Alias
- Nur Image
- custom command
- Additional volume read
- Additional volume write
- environment variables
- Wirklich gestoppt hinterher? [E]

Db Driver:
- TODO


https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory
https://docs.python.org/3/library/tempfile.html#tempfile-examples

https://www.caktusgroup.com/blog/2017/05/29/subtests-are-best/