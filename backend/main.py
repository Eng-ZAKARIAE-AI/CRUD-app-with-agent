"""Backend process entrypoint — run with: uvicorn backend.crud_app.main:app --reload."""

import uvicorn


def main() -> None:
    uvicorn.run(
        "backend.crud_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
