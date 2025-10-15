# Phase 3 Quick Test Guide

Quick reference for testing TableA component streaming.

## 🚀 Start Backend

```bash
cd C:\Users\omar.nawar\streamforge\backend
python main.py
```

Wait for:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8001
```

---

## 🧪 Run Tests

### Option 1: Full Test Suite

```bash
python test_phase3.py
```

Expected output:

```
╔═══════════════════════════════════════════════════════════════╗
║            PHASE 3 TEST SUITE - TableA Component             ║
╚═══════════════════════════════════════════════════════════════╝

✅ Backend is running and accessible

...5 tests run...

╔═══════════════════════════════════════════════════════════════╗
║                       TEST SUMMARY                            ║
╚═══════════════════════════════════════════════════════════════╝

  ✅ PASSED    - Sales Table
  ✅ PASSED    - Users Table
  ✅ PASSED    - Products Table
  ✅ PASSED    - Mixed Content
  ✅ PASSED    - Backwards Compatibility

  Total: 5/5 tests passed

  🎉 All tests passed! Phase 3 is working correctly.
```

### Option 2: Manual cURL Tests

#### Test 1: Sales Table

```bash
curl -X POST http://127.0.0.1:8001/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"show me sales table\"}"
```

#### Test 2: Users Table

```bash
curl -X POST http://127.0.0.1:8001/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"show me users table\"}"
```

#### Test 3: Products Table

```bash
curl -X POST http://127.0.0.1:8001/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"show me products table\"}"
```

#### Test 4: Backwards Compatibility (Phase 2)

```bash
curl -X POST http://127.0.0.1:8001/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"message\": \"show me a card\"}"
```

### Option 3: PowerShell

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "show me sales table"}'
```

### Option 4: Python Interactive

```python
import requests

response = requests.post(
    "http://127.0.0.1:8001/chat",
    json={"message": "show me sales table"},
    stream=True
)

for chunk in response.iter_content(decode_unicode=True):
    if chunk:
        print(chunk, end='', flush=True)
```

---

## 📋 What to Look For

### ✅ Successful TableA Stream

1. **Empty table appears first**

   ```
   $$${"type":"TableA","id":"...","data":{"columns":[...],"rows":[]}}$$$
   ```

2. **Loading text**

   ```
   Here's your sales table. Loading data ...
   ```

3. **Progressive rows (one at a time)**

   ```
   $$${"type":"TableA","id":"...","data":{"rows":[["Alice",12500,"North America"]]}}$$$
   $$${"type":"TableA","id":"...","data":{"rows":[["Bob",23400,"Europe"]]}}$$$
   ```

4. **Progress updates every 2 rows**

   ```
   Loaded 2 rows...
   ```

5. **Completion message**
   ```
   ✓ All 5 rows loaded successfully!
   ```

### ✅ Successful SimpleComponent (Phase 2)

1. **Empty component**

   ```
   $$${"type":"SimpleComponent","id":"...","data":{}}$$$
   ```

2. **Loading text with dots**

   ```
   Generating your card ...
   ```

3. **Filled component**

   ```
   $$${"type":"SimpleComponent","id":"...","data":{"title":"...","description":"...","value":150}}$$$
   ```

4. **Completion**
   ```
   All set!
   ```

---

## 🔍 Debugging

### Check Backend Logs

Backend logs show component lifecycle:

```
INFO:services.streaming_service:Pattern: TableA with progressive row streaming
INFO:services.streaming_service:Created empty table: 019... with columns: ['Name', 'Sales', 'Region']
INFO:services.streaming_service:Added 1 row(s) to table 019.... Total rows: 1
INFO:services.streaming_service:Added 1 row(s) to table 019.... Total rows: 2
...
INFO:services.streaming_service:Completed TableA streaming: 019... with 5 rows
```

### Common Issues

**1. Backend not responding**

- Check if backend is running: `http://127.0.0.1:8001/`
- Check logs for errors
- Restart: `python main.py`

**2. No components appearing**

- Check delimiter is `$$$` (not `$$`)
- Verify JSON is valid
- Check keyword detection (use "table", "sales", etc.)

**3. Rows not merging**

- Backend automatically merges rows in state tracking
- Frontend must implement merge logic separately

---

## 📊 Expected Table Data

### Sales Table

| Name             | Sales | Region        |
| ---------------- | ----- | ------------- |
| Alice Johnson    | 12500 | North America |
| Bob Smith        | 23400 | Europe        |
| Carlos Rodriguez | 34500 | Latin America |
| Diana Chen       | 18900 | Asia Pacific  |
| Ethan Brown      | 29200 | North America |

### Users Table

| Username  | Email              | Role    | Status   |
| --------- | ------------------ | ------- | -------- |
| alice_j   | alice@example.com  | Admin   | Active   |
| bob_smith | bob@example.com    | User    | Active   |
| carlos_r  | carlos@example.com | Manager | Active   |
| diana_c   | diana@example.com  | User    | Inactive |
| ethan_b   | ethan@example.com  | User    | Active   |

### Products Table

| Product       | Category    | Price   | Stock |
| ------------- | ----------- | ------- | ----- |
| Laptop Pro    | Electronics | 1299.99 | 45    |
| Desk Chair    | Furniture   | 249.99  | 120   |
| Coffee Maker  | Appliances  | 89.99   | 78    |
| Monitor 27"   | Electronics | 399.99  | 32    |
| Standing Desk | Furniture   | 549.99  | 15    |

---

## ⚙️ Configuration

All settings in `config/settings.py`:

```python
# Component types
COMPONENT_TYPES = ["SimpleComponent", "TableA"]

# Table settings
MAX_TABLE_ROWS = 20           # Max rows per table
TABLE_ROW_DELAY = 0.2         # Delay between rows (seconds)
TABLE_COLUMNS_PRESET = {      # Predefined schemas
    "sales": ["Name", "Sales", "Region"],
    "users": ["Username", "Email", "Role", "Status"],
    "products": ["Product", "Category", "Price", "Stock"]
}
```

To adjust:

1. Edit `config/settings.py`
2. Restart backend
3. Re-run tests

---

## 🎯 Next Steps

After confirming all tests pass:

1. ✅ Backend is ready
2. 🔄 Implement frontend TableA component
3. 🔄 Add row merge logic to useChat.js
4. 🔄 Register TableA in ComponentRegistry
5. ✅ Full end-to-end testing

---

**Quick tip**: Keep this guide open while developing the frontend TableA component!
