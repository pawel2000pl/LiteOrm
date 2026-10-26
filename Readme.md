# LiteORM Library 

## Overview

LiteORM is a lightweight ORM implementation for SQLite that provides thread-safe connection management and basic CRUD operations. It uses Python's threading module to maintain per-thread database connections, ensuring isolation between concurrent threads while sharing the same underlying database file.
Warning: sqlite connection cannot be used between two or more threads.


## Key Components

### Database Class

The core of LiteORM is the Database class located in FileServer/server/liteorm/database.py. It provides:
Thread-local connection management: Each thread maintains its own SQLite connection via threading.current_thread() and a per-thread dictionary (db_connections).
Connection lifecycle: Connections are created on-demand when first accessed for a given database filename.
Cursor handling: The get_cursor() method returns an existing cursor if the thread already has one, otherwise creates a new one.

### Usage Examples

#### Setup database

~~~
import liteorm
from configuration import DATABASE_FILENAME


class MainDatabase(liteorm.Database):

    database_filename = DATABASE_FILENAME
    autocommit = True


class MainDatabaseModel(liteorm.Model):

    database = MainDatabase
    skip_initialization = 1

~~~

The class `MainDatabaseModel` is not required but useful to avoid repeating `database` assignation in every model class.

#### Creating a Model

To create a table, use the `Model` class (or `Model`'s child class like `MainDatabaseModel` above) which provides SQL generation methods:
~~~
from liteorm.database import Database
from model import Model

import liteorm
import configuration
from time import time
from models import MainDatabaseModel
from libraries.filename import PROHIBITED_CHARS


class User(MainDatabaseModel):

    id: int
    name: str
    password: str
    is_admin: bool = False
    active: bool = True

    not_null = ['is_admin', 'active']
    unique_index = ['name']
    
    def before_persist(self, cursor=None):
        for c in PROHIBITED_CHARS:
            self.name = self.name.replace(c, '')
        while '..' in self.name: self.name = self.name.replace('..', '.')
        
    
~~~

The `id` column MUST BE `int`.

#### (Re)creating a Table

To recreate a table (rename, create , optionally copying values from common columns, optionally drop old table):

~~~
# User class 
User.recreate_table()
~~~


#### Updating Schema

To update schema (for example in case of updating the application) use `Model.auto_update()`. 
It scans through all imported models and tables.

#### Index Management

Indexes are managed automatically. Add field `unique_index` or ` multi_index` to your model.

#### Query data (using Model methods)

~~~
user_instance = User.query().where('Active', False).get_one()
Capability.query().where('user', user_instance).delete(commit=False)
~~~

### Available event methods in the `Model`

* before_persist
* before_update
* before_insert
* after_persist
* before_delete
* after_update
* after_insert
* after_delete

### Thread Safety

LiteORM ensures thread safety by maintaining separate connections per thread. When multiple threads access the same database file, each thread gets its own connection to avoid conflicts. However, note that concurrent writes from different threads may still cause issues depending on the SQLite configuration (e.g., check_same_thread=False).


### Error Handling

The library raises standard Python exceptions:

* `RecordNotFound`: When attempting to access a record that doesn't exist.
* `FieldNotFound`: When referencing a column or field that isn't present in the table.


