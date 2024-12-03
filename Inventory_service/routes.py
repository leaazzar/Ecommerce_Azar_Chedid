import logging
from flask import Blueprint, request, jsonify
from models import Inventory
from db import db


inventory_bp = Blueprint('inventory', __name__)

logging.basicConfig(
    filename='inventory_service.log',  # Log file
    level=logging.INFO,  # Logging level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)


@inventory_bp.route('/', methods=['GET'])
def default_route():
    """
    Default route for the Inventory Service.

    **Description:**
    This endpoint provides a welcome message to confirm that the Inventory Service is running and accessible.

    **Responses:**
    - `200 OK`: The service is running successfully.
        - `message` (str): Welcome message.
    - `500 Internal Server Error`: If an unexpected error occurs.
        - `error` (str): Detailed error message explaining the issue.

    **Examples:**
    ---
    **Request:**
    ```
    GET /
    ```

    **Successful Response:**
    ```json
    {
        "message": "Welcome to the Inventory Service!"
    }
    ```

    **Error Response (Unexpected Error):**
    ```json
    {
        "error": "An unexpected error occurred: [error details]"
    }
    ```
    """
    try:
        logging.info("Default route accessed.")
        return {"message": "Welcome to the Inventory Service!"}, 200
    except Exception as e:
        logging.error(f"Error accessing default route: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@inventory_bp.route('/inventory', methods=['POST'])
def add_goods():
    """
    Add a new item to the inventory.

    **Description:**
    This endpoint allows you to add a new item to the inventory by providing the necessary details in the request body.

    **Request Body:**
    - `name` (str): The name of the item. **Required**.
    - `category` (str): The category of the item. **Required**.
    - `price_per_item` (float): The price of a single item. Must be a number. **Required**.
    - `count_in_stock` (int): The number of items in stock. Must be a positive integer. **Required**.
    - `description` (str, optional): A brief description of the item.

    **Responses:**
    - `201 Created`: The item was successfully added to the inventory.
        - `message` (str): Confirmation message.
    - `400 Bad Request`: Invalid or missing data in the request body.
        - `error` (str): Error message explaining the issue (e.g., missing or invalid fields).
    - `500 Internal Server Error`: If an unexpected error occurs.
        - `error` (str): Detailed error message.

    **Validation:**
    - All required fields must be present in the request body.
    - `price_per_item` must be a valid number (integer or float).
    - `count_in_stock` must be a valid integer and greater than or equal to 0.

    **Examples:**
    ---
    **Request:**
    ```json
    {
        "name": "Laptop",
        "category": "Electronics",
        "price_per_item": 999.99,
        "count_in_stock": 10,
        "description": "High-performance laptop with 16GB RAM."
    }
    ```

    **Successful Response:**
    ```json
    {
        "message": "Item added successfully!"
    }
    ```

    **Error Response (Missing Field):**
    ```json
    {
        "error": "name is required."
    }
    ```

    **Error Response (Invalid Data Type):**
    ```json
    {
        "error": "price_per_item must be a number."
    }
    ```

    **Error Response (Negative Stock):**
    ```json
    {
        "error": "count_in_stock must be a positive integer."
    }
    ```

    **Error Response (Unexpected Error):**
    ```json
    {
        "error": "An unexpected error occurred: [error details]"
    }
    ```
    """
    try:
        logging.info("Request received to add a new good.")
        data = request.json

        # Validate request data
        required_fields = ['name', 'category', 'price_per_item', 'count_in_stock']
        for field in required_fields:
            if not data.get(field):
                logging.warning(f"Missing required field: {field}")
                return {"error": f"{field} is required."}, 400

        # Validate data types
        if not isinstance(data['price_per_item'], (int, float)):
            logging.warning(f"Invalid data type for price_per_item: {data['price_per_item']}")
            return {"error": "price_per_item must be a number."}, 400

        try:
            data['count_in_stock'] = int(data['count_in_stock'])
            if data['count_in_stock'] < 0:
                logging.warning(f"Invalid count_in_stock value: {data['count_in_stock']}")
                return {"error": "count_in_stock must be a positive integer."}, 400
        except ValueError:
            logging.warning(f"Invalid data type for count_in_stock: {data['count_in_stock']}")
            return {"error": "count_in_stock must be a valid integer."}, 400

        # Add the item to the database
        item = Inventory(
            name=data['name'],
            category=data['category'],
            price_per_item=data['price_per_item'],
            description=data.get('description'),
            count_in_stock=data['count_in_stock']
        )
        db.session.add(item)
        db.session.commit()

        logging.info(f"Good added successfully: {data['name']}")
        return {"message": "Item added successfully!"}, 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error while adding good: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

@inventory_bp.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_goods(item_id):
    """
    Delete an item from the inventory.

    **Description:**
    This endpoint allows you to delete an existing item from the inventory by its unique ID.

    **Path Parameter:**
    - `item_id` (int): The unique identifier of the item to be deleted.

    **Responses:**
    - `200 OK`: The item was successfully deleted from the inventory.
        - `message` (str): Confirmation message indicating the item was removed.
    - `404 Not Found`: The item with the specified `item_id` does not exist.
        - `error` (str): Error message indicating the item was not found.
    - `500 Internal Server Error`: If an unexpected error occurs during the operation.
        - `error` (str): Detailed error message.

    **Examples:**
    ---
    **Request:**
    ```
    DELETE /inventory/5
    ```

    **Successful Response:**
    ```json
    {
        "message": "Item removed successfully!"
    }
    ```

    **Error Response (Item Not Found):**
    ```json
    {
        "error": "Item not found."
    }
    ```

    **Error Response (Unexpected Error):**
    ```json
    {
        "error": "An unexpected error occurred: [error details]"
    }
    ```

    **Error Handling:**
    - If the item does not exist in the database, a `404 Not Found` response is returned.
    - In case of any other exceptions, a `500 Internal Server Error` response is returned, and the transaction is rolled back.
    """
    try:
        logging.info(f"Request received to delete item with ID: {item_id}")
        item = Inventory.query.get(item_id)

        if not item:
            logging.warning(f"Item with ID {item_id} not found.")
            return {"error": "Item not found."}, 404

        db.session.delete(item)
        db.session.commit()
        logging.info(f"Item with ID {item_id} deleted successfully.")
        return {"message": "Item removed successfully!"}, 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error while deleting item with ID {item_id}: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500

def update_goods(item_id):
    """
    Update an item's details in the inventory.

    **Description:**
    This endpoint allows you to update specific fields of an item in the inventory. Only the fields provided in the request body will be updated, while others will remain unchanged.

    **Path Parameter:**
    - `item_id` (int): The unique identifier of the item to be updated.

    **Request Body:**
    - `name` (str, optional): The updated name of the item.
    - `category` (str, optional): The updated category of the item.
    - `price_per_item` (float, optional): The updated price of a single item. Must be a valid number.
    - `count_in_stock` (int, optional): The updated stock count. Must be a positive integer.
    - `description` (str, optional): The updated description of the item.

    **Responses:**
    - `200 OK`: The item was successfully updated.
        - `message` (str): Confirmation message indicating the item was updated.
    - `400 Bad Request`: Invalid data provided in the request body.
        - `error` (str): Error message explaining the issue (e.g., invalid data types or negative stock count).
    - `404 Not Found`: The item with the specified `item_id` does not exist.
        - `error` (str): Error message indicating the item was not found.
    - `500 Internal Server Error`: If an unexpected error occurs.
        - `error` (str): Detailed error message.

    **Validation:**
    - If provided, `price_per_item` must be a valid number (integer or float).
    - If provided, `count_in_stock` must be a valid integer and greater than or equal to 0.

    **Examples:**
    ---
    **Request:**
    ```
    PUT /inventory/5
    {
        "name": "Updated Laptop",
        "price_per_item": 899.99,
        "count_in_stock": 15
    }
    ```

    **Successful Response:**
    ```json
    {
        "message": "Item updated successfully!"
    }
    ```

    **Error Response (Invalid Data Type):**
    ```json
    {
        "error": "price_per_item must be a number."
    }
    ```

    **Error Response (Negative Stock):**
    ```json
    {
        "error": "count_in_stock must be a positive integer."
    }
    ```

    **Error Response (Item Not Found):**
    ```json
    {
        "error": "Item not found."
    }
    ```

    **Error Response (Unexpected Error):**
    ```json
    {
        "error": "An unexpected error occurred: [error details]"
    }
    ```

    **Error Handling:**
    - If the item does not exist in the database, a `404 Not Found` response is returned.
    - In case of invalid data types or values, a `400 Bad Request` response is returned.
    - If any other exception occurs, a `500 Internal Server Error` response is returned, and the transaction is rolled back.
    """
    try:
        logging.info(f"Request received to update item with ID: {item_id}")
        data = request.json

        item = Inventory.query.get(item_id)
        if not item:
            logging.warning(f"Item with ID {item_id} not found.")
            return {"error": "Item not found."}, 404

        # Update fields if provided
        item.name = data.get('name', item.name)
        item.category = data.get('category', item.category)

        if 'price_per_item' in data:
            if not isinstance(data['price_per_item'], (int, float)):
                logging.warning(f"Invalid data type for price_per_item: {data['price_per_item']}")
                return {"error": "price_per_item must be a number."}, 400
            item.price_per_item = data['price_per_item']

        if 'count_in_stock' in data:
            try:
                count_in_stock = int(data['count_in_stock'])
                if count_in_stock < 0:
                    logging.warning(f"Invalid count_in_stock value: {count_in_stock}")
                    return {"error": "count_in_stock must be a positive integer."}, 400
                item.count_in_stock = count_in_stock
            except ValueError:
                logging.warning(f"Invalid data type for count_in_stock: {data['count_in_stock']}")
                return {"error": "count_in_stock must be a valid integer."}, 400

        item.description = data.get('description', item.description)
        db.session.commit()

        logging.info(f"Item with ID {item_id} updated successfully.")
        return {"message": "Item updated successfully!"}, 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error while updating item with ID {item_id}: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500
    
@inventory_bp.route('/inventory', methods=['GET'])
def get_all_goods():
    """
    Retrieve all items from the inventory.

    **Description:**
    This endpoint fetches all the items currently available in the inventory. Each item includes detailed information such as its ID, name, category, price, description, and stock count.

    **Responses:**
    - `200 OK`: Items were successfully retrieved.
        - If items exist:
            ```json
            [
                {
                    "id": 1,
                    "name": "Laptop",
                    "category": "Electronics",
                    "price_per_item": 999.99,
                    "description": "High-performance laptop.",
                    "count_in_stock": 10
                },
                {
                    "id": 2,
                    "name": "Mouse",
                    "category": "Accessories",
                    "price_per_item": 19.99,
                    "description": "Wireless mouse.",
                    "count_in_stock": 50
                }
            ]
            ```
        - If no items exist:
            ```json
            {
                "message": "No items in inventory."
            }
            ```
    - `500 Internal Server Error`: An unexpected error occurred while retrieving the inventory.
        - `error` (str): Detailed error message.

    **Examples:**
    ---
    **Request:**
    ```
    GET /inventory
    ```

    **Successful Response (With Items):**
    ```json
    [
        {
            "id": 1,
            "name": "Laptop",
            "category": "Electronics",
            "price_per_item": 999.99,
            "description": "High-performance laptop.",
            "count_in_stock": 10
        },
        {
            "id": 2,
            "name": "Mouse",
            "category": "Accessories",
            "price_per_item": 19.99,
            "description": "Wireless mouse.",
            "count_in_stock": 50
        }
    ]
    ```

    **Successful Response (No Items):**
    ```json
    {
        "message": "No items in inventory."
    }
    ```

    **Error Response:**
    ```json
    {
        "error": "An unexpected error occurred: [error details]"
    }
    ```

    **Error Handling:**
    - If the inventory is empty, a `200 OK` response is returned with a message indicating that no items are available.
    - If an unexpected error occurs, a `500 Internal Server Error` response is returned, and the error is logged.

    **Logging:**
    - Logs the number of items retrieved from the inventory.
    - Logs a warning if no items are found.
    - Logs any unexpected errors that occur during execution.
    """
    try:
        logging.info("Request received to fetch all goods.")
        items = Inventory.query.all()

        if not items:
            logging.info("No goods found in inventory.")
            return {"message": "No items in inventory."}, 200

        logging.info(f"Fetched {len(items)} goods from inventory.")
        return jsonify([{
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price_per_item": item.price_per_item,
            "description": item.description,
            "count_in_stock": item.count_in_stock
        } for item in items]), 200
    except Exception as e:
        logging.error(f"Error while fetching all goods: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}, 500