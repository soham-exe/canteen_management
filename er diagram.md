erDiagram
    %% --- Entities ---

    Menu_Items {
        int item_id PK "Item ID (PK)"
        string item_name "Item Name"
        float price "Price"
        bool is_available "Is Available?"
    }

    Orders {
        int order_id PK "Order ID (PK)"
        datetime order_time "Order Time"
        string customer_name "Customer Name"
        string status "e.g., pending, complete"
    }

    Order_Details {
        int order_detail_id PK "Detail ID (PK)"
        int order_id FK "Order ID (FK)"
        int item_id FK "Item ID (FK)"
        int quantity "Quantity"
    }

    Completed_Orders_Archive {
        int archived_order_id PK "Archived Order ID (PK)"
        int original_order_id "Original Order ID"
        datetime order_time "Order Time"
        datetime completion_time "Completion Time"
    }

    Completed_Order_Details_Archive {
        int archived_detail_id PK "Archived Detail ID (PK)"
        int original_detail_id "Original Detail ID"
        int archived_order_id "Archived Order ID"
        int item_id "Item ID"
        int quantity "Quantity"
    }

    Canteen_Status {
        int status_id PK "Status ID (PK)"
        bool is_open "Is Canteen Open?"
        string message "Display Message"
    }

    %% --- Relationships ---

    %% Live Order Relationships
    Orders ||--|{ Order_Details : "has"
    Menu_Items ||--|{ Order_Details : "is part of"

    %% Archival Process Relationships (as described)
    Orders ||..|| Completed_Orders_Archive : "archived 1-to-1"
    Order_Details ||..|{ Completed_Order_Details_Archive : "archived 1-to-N"