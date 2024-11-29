# Back-end

## Run

```
celery -A celery_app worker --loglevel=INFO
```

Running in development mode:

```bash
fastapi dev app.py
```

for production use:

```bash
fastapi run
```
