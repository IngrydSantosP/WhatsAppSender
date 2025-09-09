# Overview

This is a WhatsApp bulk messaging application built with Flask and SocketIO. The application provides a web-based interface for sending mass WhatsApp messages through an external API. Users can manage contacts with custom variables, compose personalized messages, control sending intervals, and monitor performance metrics. The application features real-time updates through WebSocket connections and includes comprehensive logging and error handling.

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