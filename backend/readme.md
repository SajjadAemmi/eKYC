# Back-end

## Run

```
celery -A tasks worker --loglevel=INFO
```

Running in development mode:

```bash
fastapi dev app.py
```

for production use:

```bash
fastapi run
```
