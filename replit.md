# Overview

Esta \u00e9 uma aplica\u00e7\u00e3o de envio de mensagens WhatsApp em massa constru\u00edda com Flask e SocketIO. A aplica\u00e7\u00e3o oferece uma interface web para envio de mensagens WhatsApp em massa atrav\u00e9s de APIs externas. Os usu\u00e1rios podem gerenciar contatos com vari\u00e1veis personalizadas, compor mensagens personalizadas, controlar intervalos de envio e monitorar m\u00e9tricas de performance. A aplica\u00e7\u00e3o possui atualiza\u00e7\u00f5es em tempo real via conex\u00f5es WebSocket e inclui logging abrangente e tratamento de erros.

## Principais Funcionalidades

### APIs Pr\u00e9-configuradas
- **Meta (Facebook) WhatsApp Business API** - API oficial do Facebook para WhatsApp Business
- **Evolution API** - API popular para automa\u00e7\u00e3o WhatsApp
- **API Personalizada** - Op\u00e7\u00e3o para configurar qualquer API customizada

### Interface Totalmente em Portugu\u00eas
- Todos os textos, mensagens e c\u00f3digos traduzidos para portugu\u00eas
- Instru\u00e7\u00f5es detalhadas para cada tipo de API
- Tooltips explicativos em todos os campos

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Single-page application** using HTML5, CSS3, and vanilla JavaScript
- **Bootstrap 5.3.0** for responsive UI components and grid system
- **Custom CSS styling** with modern gradient backgrounds and glassmorphism effects
- **Real-time updates** via Socket.IO client for live status updates and logging
- **Portuguese localization** for Brazilian market targeting

## Backend Architecture
- **Flask web framework** serving as the main application server
- **Flask-SocketIO** for real-time bidirectional communication between client and server
- **Threading system** for background message processing to prevent UI blocking
- **Queue-based message handling** with pause/resume/stop functionality
- **Modular function design** with separate validation, parsing, and API interaction methods

## Message Processing System
- **Contact parsing engine** supporting E.164 phone number format validation
- **Variable substitution system** supporting {nome} and {outro} placeholders
- **Rate limiting controls** with configurable intervals (5-60 seconds) between messages
- **Queue management** with thread-safe operations for send/pause/stop controls

## Performance Tracking
- **Multi-timeframe analytics** tracking sent/failed messages across week/semester/year periods
- **Real-time statistics updates** broadcasted to connected clients
- **Date-based performance reset** functionality for periodic reporting

## Error Handling and Validation
- **Phone number validation** using regex patterns for E.164 format
- **API response validation** with comprehensive error logging
- **Input sanitization** for all user-provided data
- **Graceful failure handling** with detailed error messages

# External Dependencies

## Core Framework Dependencies
- **Flask** - Main web application framework
- **Flask-SocketIO** - Real-time WebSocket communication
- **Requests** - HTTP client library for WhatsApp API integration

## Frontend Libraries
- **Bootstrap 5.3.0** - UI framework and responsive design
- **Bootstrap Icons 1.11.0** - Icon library for interface elements
- **Google Fonts (Inter)** - Modern typography system
- **Socket.IO Client** - Real-time client-side communication

## WhatsApp API Integration
- **Configurable endpoint** - Support for various WhatsApp API providers
- **Token-based authentication** - Secure API access management
- **Phone ID configuration** - WhatsApp Business API phone number identification

## Browser Compatibility
- **Modern browser support** - Requires ES6+ features
- **CORS configuration** - Cross-origin resource sharing enabled
- **Responsive design** - Mobile and desktop compatibility

## Development Tools
- **Python 3.x runtime** - Backend execution environment
- **Standard library modules** - datetime, threading, json, re, os, random, time