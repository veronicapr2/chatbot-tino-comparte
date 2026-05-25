from pathlib import Path


def load_text_file(path: str | Path) -> str:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {path}")

    with path.open("r", encoding="utf-8") as file:
        return file.read()


def ensure_directories(*directories: str | Path) -> None:
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)