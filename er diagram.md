# 🗂️ Entities
### 1️⃣ MENU_ITEMS
|Field Name|	Type|	Key|	Description|
|----------|-------|--------|-------|
|item_id	|INT	|PK	|Unique Item ID|
|name	|VARCHAR	|	|Item Name|
|description	|TEXT|		|Details about the item|
|price	|DECIMAL	|	|Cost of the food item|
|preparation_time	|INT|		|Time needed to prepare (minutes)|
|image_url	|VARCHAR	|	|Image of menu item|
### 2️⃣ ORDERS
|Field Name	|Type	|Key	|Description|
|----------|-------|--------|-------|
|order_id	INT	|PK	|Unique Order ID|
|customer_name|	VARCHAR	|	|Name of customer|
|total_price|	DECIMAL	|	|Total bill amount|
|order_status	|VARCHAR	|	|Pending / Preparing / Ready / Cancelled|
|order_date	|TIMESTAMP	|	|Time when order was placed|
|estimated_completion_time	|DATETIME|		|Auto-calculated completion time|
### 3️⃣ ORDER_DETAILS
|Field Name|	Type	|Key	|Description|
|----------|-------|--------|-------|
|id|	INT|	PK	|Unique Detail ID|
|order_id|	INT|	FK|	References ORDERS(order_id)|
|item_id|	INT|	FK|	References MENU_ITEMS(item_id)|
|quantity|	INT|		|Units ordered|
|price_per_item|	DECIMAL|	|	Price of 1 quantity at time of order|
### 4️⃣ COMPLETED_ORDERS_ARCHIVE
|Field Name	|Type	|Key	|Description|
|----------|-------|--------|-------|
|archived_order_id	|INT	|PK	|Archived Order ID|
|original_order_id	|INT	|	|Original Order ID|
|customer_name	|VARCHAR	|	|Customer Name|
|total_price	|DECIMAL	|    |Total Order Price|
|order_status	|VARCHAR	|	|Final status|
|order_date	|DATETIME	|	|When order was placed|
|completion_time	|DATETIME|		|When order was completed|
### 5️⃣ COMPLETED_ORDER_DETAILS_ARCHIVE
|Field Name	|Type	|Key	|Description|
|----------|-------|--------|-------|
|archived_detail_id	|INT|	PK	|Archived Detail ID|
|original_detail_id	|INT|		|Original Detail ID|
|archived_order_id	|INT|	FK	|Link to archived order|
|item_id	|INT|		|Menu item reference|
|quantity	|INT|		|Quantity ordered|
|price_per_item	|DECIMAL|		|Price of item|
### 6️⃣ CANTEEN_STATUS
|Field Name	|Type	|Key	|Description|
|----------|-------|--------|-------|
|status_id|	INT|	PK|	ID|
|is_open|	BOOL|		|Whether canteen is open|
|message|	TEXT|		|Display message|
### 🔗 Relationships
```bash
MENU_ITEMS           1 ────<  ORDER_DETAILS  >──── 1  ORDERS

ORDERS               1 ────<  ORDER_DETAILS

ORDERS               1 ─────── 1  COMPLETED_ORDERS_ARCHIVE
ORDER_DETAILS        1 ────<      COMPLETED_ORDER_DETAILS_ARCHIVE
```
### Relationship Summary

- One Order can contain many Order Details

- One Menu Item can appear in many Order Details

- Orders ⇢ Archive is 1-to-1

- Order Details ⇢ Archive Details is 1-to-many

- Canteen Status is a single global record table