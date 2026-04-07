# python-toolkit

## Description

Custom python tooling packages that contain generic config and helper classes and functions used across multiple projects

## Contents

* `pleasant_loggers`: custom logging setup package with compacted customizability of logging features including the addition of JSON logging for machine readability as well as a simple JSON log parser.
* `pleasant_database`: SQLAlchemy based local database wrapper classes and functions to make database setup and CRUD easy in new projects.
* `pleasant_errors`: lightweight error-handling package that brings Rust-style `Result` types (`Ok`/`Err`) and a decorator-based `@catch` to Python, making error paths explicit without scattering try/except blocks throughout your code.

## Usage

Install via pip with `pip install git+https://github.com/EliasRodkey/python-toolkit`.
Import subpackages using normal import statements. Each sub package has it's own detailed README.md files with more information on usage
as well as a suite of tests to ensure that it is running properly on your system.
