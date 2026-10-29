# Library for site generation


# Environment setup
```sh
python3 -m venv python_environment
source python_environment/bin/activate
pip install poetry


poetry install

```

Other commands
```sh
alias tree='tree -I "python_environment|__pycache__"'

tar cvf site.tar   --exclude="*/__pycache__"   --exclude="site_generator/python_environment/*" --exclude="**/.mypy_cache" --exclude="*/.pytest_cache" --exclude="*/.git" --exclude="*/.ruff_cache"  --exclude="site_generator/htmlcov" --exclude="site_generator/.coverage" site_generator/
```
