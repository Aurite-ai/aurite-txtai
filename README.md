# Aurite TxtAI Service

## Overview

This project is currently being refactored from a monolithic data processing pipeline into a microservice architecture. The TxtAI service handles AI-powered data processing and trend analysis, focusing on content categorization, trend detection, and insight generation.

## Current Status

The project is in active refactoring with the following components established:

- ✅ Database infrastructure
- ✅ Development environment setup
- ✅ Basic project structure
- 🔄 Service architecture (in progress)
- 📝 API endpoints (planned)

## Project Structure

```
.
├── data_processors/
│   ├── __init__.py
│   ├── base_processor.py
│   └── technology_processor.py
├── tests/
│   └── test_technology_processor.py
├── txtai/
│   ├── __init__.py
│   └── client.py
├── requirements.txt
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- txtai for providing the underlying NLP capabilities.

## Development Commands

```bash
just db-setup # Initial database setup
just db-init # Initialize schema
just db-reset # Reset databases
just db-migrate # Run migrations
just db-test # Run database tests
```

```bash
just test # All tests
just test-db # Database tests
just test-api # API tests
```
