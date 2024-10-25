from database.mongodb import get_database

def init_menu_data():
    db = get_database()
    menu_items = [
        {
            "name": "Margherita Pizza",
            "description": "Classic tomato and mozzarella pizza",
            "price": 12.99,
            "category": "Pizza",
            "available": True
        },
        {
            "name": "Chicken Burger",
            "description": "Grilled chicken with fresh vegetables",
            "price": 8.99,
            "category": "Burgers",
            "available": True
        }
    ]
    
    db.menu.insert_many(menu_items)

# Run this once to initialize menu data
if __name__ == "__main__":
    init_menu_data()