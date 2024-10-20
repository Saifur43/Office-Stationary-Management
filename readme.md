# Office Stationary Management

## Overview

This project is a simple inventory management system built using Django. It allows users to manage inventory items, submit requisitions, and enables admin users to approve or reject requisitions. The system also tracks inventory levels and generates reports based on requisition data.

## Features

- **Inventory Management**: Add, update, and track items in the inventory.
- **Requisition Submissions**: Users can submit requisitions for items.
- **Admin Approval**: Admins can approve or reject requisitions and adjust the quantities.
- **Tracking**: Keep track of requested and approved quantities.
- **Reporting**: Generate reports filtered by user, item, or date range, and export them as PDFs.
- **User Dashboard**: A dashboard for users to track their own requisitions.
- **Admin Dashboard**: Admin dashboard with quick links to manage requisitions, view reports, and add new inventory items.

## Installation

### Prerequisites

Ensure you have the following installed on your machine:

- Python 3.x
- Django 3.x or later
- PostgreSQL or another database (can use SQLite for development)
- pip (Python package installer)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/inventory-management-system.git
   cd inventory-management-system
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create a `.env` file in the project root and add the following settings:
     ```
     DEBUG=True
     SECRET_KEY=your-secret-key
     DATABASE_URL=postgres://username:password@localhost:5432/yourdb
     ```

5. **Migrate the database**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

   Open a browser and navigate to `http://127.0.0.1:8000/`.


## Key Models

- `InventoryItem`: Represents an item in the inventory.
- `Category`: Represents the category of inventory items.
- `Requisition`: Represents a requisition request made by a user.
- `RequisitionItem`: Tracks the items and quantities requested and approved in each requisition.

## Key Views

- `RequisitionListView`: Displays the list of requisitions for users.
- `ApproveRequisitionView`: Admin view for approving or rejecting requisitions.
- `StatisticsView`: View for displaying statistics on approved items.
- `ReportView`: Generates reports with filtering options (by user, item, and date range) and allows exporting to PDF.

## Custom Forms

The project uses Django's crispy forms to enhance form layouts and uses custom filtering forms in reports.

## Usage

### Adding Items
- Admins can add new inventory items by navigating to the "Add Item" page.

### Submitting Requisitions
- Users can submit requisitions by selecting the desired items and entering the requested quantity.

### Approving Requisitions
- Admin users can approve or reject requisitions. Approved quantities will be deducted from the total inventory.

### Reports
- Admins can generate reports based on user, item, and date filters. The results can also be exported to PDF.


## License

This project is licensed under the MIT License. See the `LICENSE` file for details.