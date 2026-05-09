#!/usr/bin/env python
"""
Main entry point for backend server
Run with: python main.py
"""
import uvicorn


def main():
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
    )


if __name__ == "__main__":
    main()
