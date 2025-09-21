# Crawl Resume Feature

The Web Crawler now supports resuming interrupted crawls, making it perfect for large-scale crawling projects that might take hours or days to complete.

## How It Works

The crawler automatically saves its state every 10 pages crawled, including:
- **Visited URLs**: All URLs that have been processed
- **Queue State**: Pending URLs waiting to be crawled
- **Progress Statistics**: Pages downloaded, errors encountered
- **Configuration**: Original crawl settings

## Usage

### Starting a New Crawl
```bash
python crawler.py https://example.com
```
The crawler automatically creates a session and saves state as it progresses.

### Listing Incomplete Sessions
```bash
python crawler.py --list-sessions
```
Shows all sessions that can be resumed:
```
Incomplete crawl sessions that can be resumed:
============================================================
Session 1: https://example.com
  Status: interrupted
  Started: 2025-09-21 10:30:15
  Progress: 25/100 pages
  Resume with: python crawler.py --resume 1
```

### Resuming a Crawl
```bash
python crawler.py --resume 1
```
Continues from where the crawler left off, including:
- ✅ Restores visited URLs (no re-crawling)
- ✅ Restores pending queue
- ✅ Restores progress counter
- ✅ Uses original configuration settings

### Resume with Configuration Override
```bash
python crawler.py --resume 1 --workers 5 --max-pages 200
```
Resume the session but with modified settings (more workers, higher page limit).

## When State is Saved

The crawler saves state in these situations:
1. **Every 10 pages** - Automatic periodic saves
2. **User interruption** (Ctrl+C) - Clean shutdown with state save
3. **Completion** - Final state save when crawl finishes
4. **Errors** - State preserved even if crawler encounters issues

## Database Integration

Resume functionality requires database storage:
- **Enabled by default** - All sessions are tracked
- **SQLite database** stored in `downloaded_pages/crawler_data.db`
- **Thread-safe** - Works with concurrent crawling
- **Persistent** - Survives system restarts

## Resume Examples

### Basic Resume Workflow
```bash
# Start crawling
python crawler.py https://example.com --max-pages 100

# Interrupted at page 25... Press Ctrl+C
# [INFO] Crawling interrupted by user
# [INFO] Saving crawl state for resume...
# [INFO] Session 1 marked as interrupted. Use --resume 1 to continue.

# Later, resume the crawl
python crawler.py --resume 1
# [RESUME] Resuming session 1 from https://example.com
# [RESUME] Visited URLs: 25
# [RESUME] Pages downloaded: 25
# [RESUME] Pending URLs in queue: 47
```

### Large Site Crawling
```bash
# Start a large crawl that might take hours
python crawler.py https://large-site.com --max-pages 1000 --workers 5

# Can be safely interrupted and resumed multiple times
python crawler.py --resume 2  # Continue where you left off
```

### Checking Available Sessions
```bash
# See what can be resumed
python crawler.py --list-sessions

# Resume the most recent session
python crawler.py --resume 3
```

## Benefits

### 🚀 **Efficiency**
- No duplicate work - never re-crawls visited URLs
- Fast startup - immediately continues from last position
- Preserves expensive network requests and processing

### 🛡️ **Reliability** 
- Survives system crashes, network outages, power failures
- Graceful handling of interruptions (Ctrl+C)
- Data integrity with SQLite ACID compliance

### ⏱️ **Time Saving**
- Essential for multi-hour crawling sessions
- Perfect for overnight/weekend crawls
- Allows experimentation with settings without losing progress

### 🔧 **Flexibility**
- Can modify settings when resuming (workers, limits, delays)
- Multiple sessions can be managed independently
- Easy session identification and management

## Technical Details

### State Storage
- **Sessions Table**: Tracks crawl metadata and configuration
- **Queue State Table**: Stores pending URLs with depth information
- **Pages Table**: Records all crawled pages (prevents re-crawling)
- **JSON State**: Compact storage of visited URL sets

### Thread Safety
- All state operations are thread-safe with locks
- Concurrent workers safely share state updates
- Queue inspection doesn't block crawling operations

### Performance Impact
- **Minimal overhead** - state saves every 10 pages only
- **Non-blocking** - state saves don't interrupt crawling
- **Efficient storage** - optimized database operations

## Configuration File Support

Resume works with YAML configuration files:

```yaml
# crawler_config.yaml
crawler:
  max_pages: 500
  delay: 1.5
  max_workers: 4
```

```bash
# Original crawl with config
python crawler.py https://example.com --config crawler_config.yaml

# Resume still uses original config (unless overridden)
python crawler.py --resume 1
```

## Error Handling

The resume feature handles various error conditions:
- **Missing session**: Clear error message if session ID doesn't exist
- **Corrupted state**: Falls back to fresh crawl if state is invalid
- **Database issues**: Graceful degradation with warnings
- **Network problems**: Can resume after connectivity is restored

## Limitations

- **Database required**: Resume doesn't work with `--no-database` flag
- **Large queue memory**: Very large queues (10k+ URLs) may use significant memory
- **Session cleanup**: Old sessions aren't automatically deleted (manual cleanup needed)

This feature makes the Web Crawler suitable for production use and large-scale data collection projects.