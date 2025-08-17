# Testing Guide for Mercor Airtable Automation System

This document provides a comprehensive guide to the testing infrastructure for the Mercor Airtable Automation System.

## Overview

The project includes a robust testing suite with:

- **Unit tests** for individual module functionality
- **Integration tests** for workflow between modules
- **Performance tests** for scalability and rate limiting
- **Automated testing** via GitHub Actions CI/CD
- **Code coverage** reporting and analysis

## Test Structure

```
mercor-airtable-automation/
├── test_basic.py           # Original basic tests
├── test_unit.py           # Comprehensive unit tests
├── test_integration.py    # Integration and workflow tests
├── test_performance.py    # Performance and scalability tests
├── test_fixtures.py       # Test data and mock fixtures
├── conftest.py            # Pytest configuration and shared fixtures
├── pytest.ini            # Pytest configuration
├── .coveragerc           # Coverage configuration
├── tox.ini               # Multi-environment testing configuration
└── Makefile              # Test automation commands
```

## Running Tests

### Quick Commands (via Makefile)

```bash
# Install development dependencies
make install-dev

# Run all tests
make test

# Run specific test types
make test-unit            # Unit tests only
make test-integration     # Integration tests only
make test-performance     # Performance tests only

# Run tests with coverage
make test-coverage

# Quick development test
make quick-test

# Validate configuration
make validate
```

### Direct pytest Commands

```bash
# Run all tests
pytest

# Run specific test files
pytest test_unit.py -v
pytest test_integration.py -v
pytest test_performance.py -v

# Run specific test classes or methods
pytest test_unit.py::TestConfig -v
pytest test_unit.py::TestConfig::test_config_validation_success -v

# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run tests with specific markers
pytest -m "unit" -v
pytest -m "integration" -v
pytest -m "performance" -v
```

### Multi-environment Testing (via tox)

```bash
# Install tox
pip install tox

# Run tests across multiple Python versions
tox

# Run specific environments
tox -e py39              # Python 3.9
tox -e flake8            # Linting
tox -e mypy              # Type checking
tox -e coverage          # Coverage analysis
```

## Test Categories

### 1. Unit Tests (`test_unit.py`)

Tests individual components in isolation:

- **Configuration**: Environment variable validation, constants, table names
- **JSON Compression**: Data retrieval, compression logic, error handling
- **Shortlisting**: Criteria evaluation, currency conversion, business logic
- **LLM Evaluation**: Prompt generation, response parsing, API retry logic
- **Main Orchestrator**: Pipeline coordination, status reporting
- **Utilities**: JSON validation, data generation, edge cases

**Key Features:**
- Comprehensive mocking of external dependencies
- Edge case testing
- Error handling verification
- Business logic validation

### 2. Integration Tests (`test_integration.py`)

Tests module interactions and data flow:

- **End-to-end workflows**: Complete pipeline execution
- **Data consistency**: JSON compression/decompression roundtrips
- **Module integration**: Data flow between components
- **Error propagation**: Graceful failure handling across modules
- **Batch processing**: Multiple applicant processing

**Key Features:**
- Realistic workflow simulation
- Data integrity verification
- Cross-module interaction testing
- Performance under realistic conditions

### 3. Performance Tests (`test_performance.py`)

Tests system performance and scalability:

- **Large dataset handling**: 100-500 record processing
- **API rate limiting**: Retry mechanisms and backoff strategies
- **Concurrent operations**: Thread safety and parallel processing
- **Memory efficiency**: Large JSON object handling
- **Resource utilization**: Connection pooling and cleanup

**Key Features:**
- Scalability validation
- Rate limit simulation
- Concurrent execution testing
- Memory usage optimization

### 4. Test Fixtures (`test_fixtures.py`)

Provides reusable test data:

- **Sample data**: Realistic applicant profiles
- **Test cases**: Shortlisting criteria scenarios
- **Mock responses**: LLM evaluation examples
- **Random generators**: Dynamic test data creation
- **Airtable records**: Mock database structures

**Key Features:**
- Realistic test data
- Parameterized test scenarios
- Randomized testing capabilities
- Consistent mock structures

## Test Configuration

### Environment Variables

Tests automatically set up required environment variables:

```python
# Automatically set in conftest.py
AIRTABLE_API_KEY = 'test_key'
AIRTABLE_BASE_ID = 'test_base'
OPENAI_API_KEY = 'test_openai'
```

### Mocking Strategy

- **External APIs**: All Airtable and OpenAI calls are mocked
- **File I/O**: No actual file system operations during testing
- **Time-dependent**: Time.sleep() calls are mocked for speed
- **Random data**: Seeded for reproducible results

### Coverage Requirements

- **Minimum coverage**: 80% (configured in pytest.ini)
- **Coverage exclusions**: Test files, virtual environments, generated files
- **Reports**: HTML, XML, and terminal output available

## Continuous Integration

### GitHub Actions Workflow

The project includes automated testing via GitHub Actions:

```yaml
# .github/workflows/test.yml
- Multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Automated dependency installation
- Linting with flake8
- Type checking with mypy
- Security scanning with bandit
- Test execution with coverage reporting
- Artifact upload for reports
```

### Workflow Triggers

- **Push**: to main/develop branches
- **Pull requests**: to main branch
- **Manual**: on-demand execution

## Best Practices

### Writing Tests

1. **Isolation**: Each test should be independent
2. **Descriptive names**: Clear test method naming
3. **Arrange-Act-Assert**: Standard test structure
4. **Mock external dependencies**: No real API calls
5. **Test edge cases**: Empty data, errors, boundary conditions

### Test Data

1. **Use fixtures**: Leverage `test_fixtures.py` for common data
2. **Realistic data**: Test with production-like scenarios
3. **Parameterized tests**: Test multiple scenarios efficiently
4. **Random testing**: Use generators for diverse test cases

### Performance Testing

1. **Reasonable limits**: Set appropriate time/resource limits
2. **Mock delays**: Speed up tests by mocking time.sleep()
3. **Resource cleanup**: Ensure proper cleanup after tests
4. **Scalability focus**: Test with realistic data volumes

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

**Module Import Issues**
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=.
```

**Mock-related Failures**
```bash
# Check that all external dependencies are properly mocked
# Verify environment variables are set correctly
```

**Performance Test Timeouts**
```bash
# Increase timeout limits in pytest.ini if needed
# Check that time.sleep() calls are properly mocked
```

### Debug Mode

```bash
# Enable verbose logging
pytest --verbose --tb=short

# Run specific failing test
pytest test_unit.py::TestConfig::test_config_validation_success -v -s

# Debug with pdb
pytest --pdb
```

## Development Workflow

### Before Committing

```bash
# Run quick tests
make quick-test

# Run full test suite
make test

# Check code quality
make lint
make type-check
make security

# Generate coverage report
make test-coverage
```

### Adding New Tests

1. **Create test methods** in appropriate test files
2. **Use existing fixtures** from `test_fixtures.py`
3. **Follow naming conventions**: `test_<functionality>_<scenario>`
4. **Add appropriate mocks** for external dependencies
5. **Update documentation** if adding new test categories

### Test Maintenance

1. **Regular updates**: Keep test data current with system changes
2. **Performance monitoring**: Watch for test execution time increases
3. **Coverage monitoring**: Maintain high code coverage
4. **Mock updates**: Update mocks when APIs change

## Metrics and Reporting

### Coverage Reports

- **HTML report**: `htmlcov/index.html` (after running coverage tests)
- **Terminal output**: Immediate feedback during test runs
- **XML report**: `coverage.xml` for CI/CD integration

### Performance Metrics

- **Execution time**: Tracked for performance regression detection
- **Memory usage**: Monitored during large dataset tests
- **API call patterns**: Verified for rate limiting compliance

### Quality Metrics

- **Test count**: Currently 50+ comprehensive tests
- **Coverage percentage**: Target 80%+ code coverage
- **Test types**: Unit (70%), Integration (20%), Performance (10%)

This testing infrastructure ensures high code quality, reliable functionality, and maintainable codebase for the Mercor Airtable Automation System.
