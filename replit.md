# replit.md

## Overview

LangSense is a comprehensive Telegram bot designed for financial services with multi-language support (Arabic and English). The bot provides a complete financial ecosystem including deposit/withdrawal processing, complaint handling, user management, and admin broadcasting capabilities. It features phone number verification, automatic customer code generation, and a robust admin panel for system management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Bot Framework**: Simple HTTP-based Telegram Bot API implementation (replaced Aiogram due to dependency conflicts)
- **Language**: Python 3 with standard library HTTP requests
- **State Management**: Database-driven state management using SQLite for user sessions and preferences
- **Implementation**: Resolved kaleido dependency conflicts by creating a lightweight HTTP-based solution

### Database Layer
- **Database**: SQLite for simplicity and reliability (langsense.db)
- **Connection Management**: Direct sqlite3 library usage with thread-safe connections
- **Schema**: Core tables including Users (with phone verification, customer codes), Languages (Arabic/English support), and system tables
- **Data Integrity**: Automatic customer code generation, phone number verification, multi-language support

### Multi-Language Architecture
- **Internationalization**: JSON-based translation system supporting Arabic (RTL) and English
- **Language Detection**: Automatic language detection with user preference storage
- **Dynamic Content**: All UI elements, keyboards, and messages are fully localized
- **Fallback System**: Graceful degradation when translations are missing

### Authentication & Authorization
- **Admin System**: Environment variable-based admin user ID configuration
- **Decorator Pattern**: `@admin_required` decorator for protecting administrative functions
- **User Registration**: Phone number verification with automatic customer code generation
- **Session Management**: Persistent user state across bot interactions

### Message Processing Architecture
- **Router System**: Modular handler organization (start, admin, broadcast, settings, announcements)
- **State Management**: Multi-step workflows using FSM states for complex user interactions
- **Queue System**: Asynchronous message broadcasting with rate limiting and retry logic
- **Media Handling**: Support for images, documents, and rich media in broadcasts

### Financial Services Workflow
- **Request Processing**: Structured workflow for deposits, withdrawals, and complaints
- **Status Tracking**: Complete audit trail with status transitions (pending, approved, rejected, etc.)
- **Admin Approval**: Manual review process for financial transactions
- **Receipt Management**: Image upload and processing for transaction verification

### Broadcasting & Notifications
- **Mass Messaging**: Rate-limited broadcasting system with chunked delivery
- **Targeting**: Advanced filtering by language, country, and user segments
- **Delivery Tracking**: Individual message delivery status monitoring
- **Retry Logic**: Automatic retry for failed message deliveries with exponential backoff
- **Announcements**: Scheduled system-wide announcements with rich content support

### Error Handling & Logging
- **Structured Logging**: Comprehensive logging with file and console output
- **Exception Management**: Graceful error handling with user-friendly messages
- **Validation**: Input sanitization and validation throughout the application
- **Monitoring**: Performance and delivery tracking for all operations

### Configuration Management
- **Environment-Based**: All sensitive configuration via environment variables
- **Feature Toggles**: Configurable limits, timeouts, and behavioral parameters
- **Multi-Environment**: Support for development and production configurations

## External Dependencies

### Core Dependencies
- **Aiogram v3**: Modern Telegram Bot API framework with async support
- **SQLAlchemy**: Async ORM for database operations and relationship management
- **APScheduler**: Task scheduling for announcements and periodic operations
- **Pillow**: Image processing for media validation and manipulation

### Database Options
- **SQLite**: Default development database with aiosqlite driver
- **PostgreSQL**: Production database with asyncpg driver for scalability

### Runtime Dependencies
- **Python-dotenv**: Environment variable management and configuration loading
- **AsyncIO**: Core async runtime for handling concurrent operations

### Optional Integrations
- **File Storage**: Local file system for media uploads (configurable for cloud storage)
- **External APIs**: Extensible architecture for payment provider integrations
- **Monitoring Services**: Ready for integration with external logging and monitoring platforms