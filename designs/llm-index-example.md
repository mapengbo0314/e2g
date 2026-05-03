# Overview
The Meridian Payments Platform is a microservices-based system designed to streamline global financial transactions and merchant onboarding. This system provides a centralized API interface, defined in the `proto` subdirectory, that orchestrates complex workflows across multiple services including `auth` for identity management, `ledger` for transaction tracking, and `gateway` for external payment provider integration. By automating tasks such as merchant verification, transaction routing, and settlement, the platform reduces the manual effort required for financial operations.

Architecturally, the project is organized into specialized components. The `service` subdirectory contains the core business logic implemented as gRPC services, which leverage shared utilities in `common` for database interactions, cryptography, and logging.

The `client` subdirectory provides the necessary communication layers for external consumers, while `server` functions as the composite node for assembling the service into a deployable container. This structure facilitates a modular approach to financial orchestration, supported by an asynchronous event-driven framework that manages the dependencies between various transaction states.

# Deep Dive
The Meridian Payments Platform implements a robust set of services to manage the complex requirements of global payments. Instead of fragmented processes, this platform provides a unified interface that orchestrates changes in financial ledgers, risk management systems, and settlement platforms.

### Core Orchestration Pattern
Most operations within this platform follow a consistent asynchronous pattern. A typical transaction workflow involves:
1. **Input Validation and Transformation**: Parameters from the request are converted into standardized identifiers, ensuring consistency across the ledger and risk engines.
2. **Configuration Generation**: The system uses shared templates to generate transaction metadata and settlement instructions.
3. **Ledger Automation**: Changes are automatically committed to the ledger, which maintains an immutable record of all transactions.
4. **Multi-System Provisioning**: For new merchant onboarding, the platform parallelizes calls to external KYC (Know Your Customer) providers, risk assessment engines, and bank account verification services.

### Event-Driven Architecture
A unique aspect of this codebase is the `TransactionFlowManager`, which manages state transitions for payments. It implements a state machine that monitors event streams, handles retries for transient failures, and ensures eventual consistency across distributed services.

# Architectural Patterns
The codebase follows a clean, modular architecture where business logic is encapsulated in service handlers within the `service/` directory. A significant pattern is the orchestration of multiple external providers through an event-driven framework. The `Common` utility library is central for maintaining consistent data models across services. One notable implementation detail is the `RetryHandler` in the `gateway` service, which handles exponential backoff and circuit breaking for unreliable external payment APIs.

# Key Components
- **service/**: Core implementation of the payment services. Handles merchant registration, transaction processing, and settlement logic.
- **common/**: Shared library providing utilities for encryption, database access, and standardized logging.
- **proto/**: Protocol buffer definitions for all service interfaces and data models.
- **client/**: Auto-generated client libraries for consuming the payments API.
- **server/**: Deployment configuration and entry point for the service containers.

# Key Interfaces
- `MeridianPaymentsService`: The primary API interface for processing transactions and managing accounts.
- `LedgerClient`: Abstraction layer for interacting with the immutable transaction ledger.
- `RiskEngine`: Interface for performing real-time fraud detection and risk assessment.

# Key Dependencies
- **gRPC**: Foundation for all service communication.
- **PostgreSQL**: Primary data store for user profiles and non-transactional data.
- **Redis**: Used for distributed locking and caching.
- **Kafka**: Event bus for asynchronous service-to-service communication.