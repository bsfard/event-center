# Launching Event Center

## How to

- [Launch Event Center](#launch-event-center)

### Launch Event Center

```shell

# Set environment variables.
export EC_PORT=6000       # set event center port

export EC_LOG_DEBUG=1     # =1            : log DEBUG messages to console
                          # <>1, (unset)  : log INFO messages to console
                          
cd eventcenter
PYTHONPATH=../ gunicorn -w 4 -b 0.0.0.0:$EC_PORT eventcenter.app_event_center:app
```
