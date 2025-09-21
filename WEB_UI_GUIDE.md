# Web Crawler UI Guide

## 🌐 Web Interface

The Web Crawler now includes a professional web interface that runs alongside the terminal version. Both interfaces access the same database and work together seamlessly.

## 🚀 Quick Start

### Start the Web UI:
```bash
python web_ui.py
```

Then open your browser to: **http://localhost:5000**

### Terminal Still Works:
```bash
python crawler.py https://example.com --max-pages 50
```

Both interfaces share the same data and can be used simultaneously!

## 📊 Features

### 🏠 Dashboard
- **Live Statistics**: Total pages, active crawls, success rates, errors
- **Quick Start Form**: Start crawls with a simple form
- **Recent Crawls**: View past crawl sessions with status
- **Auto-refresh**: Stats update every 30 seconds

### 👁️ Live Monitor
- **Real-time Progress**: Watch crawls in progress
- **Live Statistics**: Pages/sec, data size, errors, elapsed time  
- **Performance Charts**: Visual progress tracking
- **Activity Log**: See what URLs are being processed
- **Stop/Resume**: Control running crawls

### 📋 Results Browser
- **Paginated Results**: Browse all crawled data
- **Advanced Filtering**: Filter by session, domain, status
- **Search & Sort**: Find specific pages quickly
- **Status Indicators**: Visual success/error status
- **Export Integration**: Generate exports directly from browser

### 📊 Export & Reporting
- **Multiple Formats**: CSV, JSON, HTML reports
- **Session Filtering**: Export specific crawl sessions
- **Statistics**: Include performance metrics
- **Professional Reports**: HTML reports with charts and insights

## 🎯 Benefits

### **Hybrid Approach**
- **Web UI**: For monitoring, browsing, and analysis
- **Terminal**: For automation, scripting, and power users
- **Shared Data**: Both access the same SQLite database

### **User-Friendly**
- **No Command Line**: Point-and-click crawling
- **Visual Feedback**: Progress bars, charts, statistics  
- **Professional Interface**: Modern, responsive design
- **Error Handling**: Clear error messages and status

### **Advanced Features**
- **Real-time Updates**: See progress as it happens
- **Export Tools**: Generate reports easily
- **Session Management**: Track and resume crawls
- **Data Analysis**: Browse and filter results

## 🔧 Technical Details

### **Architecture**
- **Frontend**: HTML5, Bootstrap 5, Chart.js
- **Backend**: Python Flask, SQLite database
- **Real-time**: WebSocket support (when available)
- **Integration**: Uses existing crawler.py engine

### **File Structure**
```
Web-Crawler/
├── web_ui.py           # Flask web server
├── crawler.py          # CLI crawler (unchanged)
├── templates/          # HTML templates
│   ├── base.html      # Base template with styling
│   ├── dashboard.html # Main dashboard
│   ├── monitor.html   # Live monitoring
│   └── results.html   # Results browser
└── downloaded_pages/   # Shared data directory
    └── crawler_data.db # Shared SQLite database
```

### **Dependencies**
```
flask>=2.3.0
flask-socketio>=5.3.0  # For real-time updates (optional)
```

## 🎮 Usage Examples

### **Web UI Workflow:**
1. Open browser to `http://localhost:5000`
2. Enter URL and settings in Quick Start form
3. Click "Start Crawling"
4. Monitor progress in real-time
5. Browse results and generate exports

### **Terminal Workflow (still works):**
```bash
python crawler.py https://example.com --max-pages 100 --workers 5
python data_exporter.py --format html --session 20
```

### **Mixed Workflow:**
```bash
# Start crawl in terminal
python crawler.py https://api-docs.com --workers 3 &

# Monitor progress in web browser
# http://localhost:5000/monitor/session_21

# Browse results in web UI when complete
```

## ⚙️ Configuration

The web UI inherits all crawler settings from `crawler_config.yaml`:
- User agents, delays, timeouts
- Content filtering rules
- Database settings
- Export preferences

## 🛡️ Security Notes

- **Development Server**: The included server is for development only
- **Local Access**: Default binding is localhost (127.0.0.1)
- **Production**: Use a proper WSGI server (gunicorn, uwsgi) for production
- **Firewall**: Ensure port 5000 is properly secured if exposing externally

## 🏁 Conclusion

The Web Crawler UI provides the best of both worlds:
- **Professional web interface** for everyday use
- **Powerful terminal interface** for automation
- **Shared data and seamless integration**
- **Modern, responsive design** with real-time updates

Whether you prefer clicking buttons or typing commands, the Web Crawler has you covered! 🕷️✨