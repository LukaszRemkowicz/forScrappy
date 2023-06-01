
# Concept
It's a private project, which core use case is to get download links from some forum. Written in clean architecture.

## configuration

Change the name of example.env to .env and fill it with your data.

# How to play?

docker:
```bash
docker-compose up --build
docker-compose run --rm forscrappy sh -c "python cli.py {command}"
```
cmd/terminal:

```bash
pipenv install
pipenv shell
python cli.py + command
```

### Tests

```bash
pipenv install --dev
pytest
```
