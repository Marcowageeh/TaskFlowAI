# replit.md

## Overview

LangSense is a streamlined Telegram bot for financial services with Arabic support. The bot provides a simplified financial ecosystem focusing on deposit/withdrawal processing with company selection, wallet number input, and exchange address management. Features include user registration, admin approval system, and comprehensive transaction tracking.

## User Preferences

Preferred communication style: Simple, everyday language.
UI Design: Button-based navigation preferred over text commands.
Notifications: Only at completion of operations, not during process.
Admin Commands: Simplified format without complex syntax requirements.

## System Architecture

### Core Framework
- **Bot Framework**: Simplified HTTP-based Telegram Bot API implementation using Python standard library
- **Language**: Python 3 with urllib and json for lightweight operation
- **State Management**: Simple dictionary-based state management for user sessions
- **Implementation**: Streamlined single-file solution without external dependencies

### Database Layer
- **Database**: CSV files for simplicity and transparency
- **Files**: users.csv, transactions.csv, companies.csv, exchange_addresses.csv
- **Schema**: Simplified tables focusing on essential data only
- **Data Integrity**: Automatic customer code generation, basic validation

### User Interface
- **Navigation**: Button-based keyboards for all interactions
- **Language**: Arabic primary with simple interface
- **Flow**: Linear process flows for deposits and withdrawals
- **Simplicity**: No complex commands or syntax requirements

### Authentication & Authorization
- **Admin System**: Environment variable-based admin user ID configuration
- **User Registration**: Name and phone number only
- **Session Management**: Simple state tracking for multi-step processes

### Financial Services Workflow
- **Deposit Process**: Company Selection → Wallet Number → Amount → Completion
- **Withdrawal Process**: Company Selection → Wallet Number → Amount → **Withdrawal Address Entry** → **Confirmation Code Entry** → Final Confirmation
- **Status Tracking**: Simple pending/approved/rejected states
- **Admin Approval**: Direct text-based commands (موافقة/رفض)
- **Withdrawal Address**: Users must specify withdrawal address for each request
- **Confirmation Code**: Required verification code from customer before processing

### Company & Address Management
- **Company Management**: Simple add/delete commands without complex formatting
- **Exchange Address**: Single active address that can be updated easily
- **Flexibility**: Dynamic company list for both deposits and withdrawals

### Notifications
- **Timing**: Only at completion of operations (approval/rejection) + instant notifications for new requests
- **Content**: Essential information only
- **Direction**: Bidirectional (admin ↔ user) at completion + instant admin alerts for new transactions
- **Admin Alerts**: Immediate notifications when users submit deposit/withdrawal requests
- **Customer Alerts**: Instant notifications upon approval/rejection with full transaction details

### Admin Interface
- **Commands**: Simplified text-based commands
- **Format**: Natural language without complex syntax
- **Examples**: "موافقة DEP123", "رفض WTH456 سبب", "اضف_شركة اسم نوع تفاصيل"
- **Navigation**: Button-based admin panel

### Error Handling & Logging
- **Logging**: Basic console logging for monitoring
- **Validation**: Simple input validation with clear error messages
- **Fallbacks**: Graceful handling of invalid inputs

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