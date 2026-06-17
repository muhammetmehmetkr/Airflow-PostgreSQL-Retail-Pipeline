# Airflow Homework CSV → PostgreSQL with Hourly Refresh

## Business problem
Business units X, Y, Z need to track order status on a product basis:
*"Was product YY in order XX delivered? Has it been paid? Has it been cancelled?"*

They want a single view they can query, refreshed **every hour**.

## Source data
Three CSV files from [`erkansirin78/datasets/retail_db`](https://github.com/erkansirin78/datasets/tree/master/retail_db):

| File | Becomes table |
|:---|:---|
| `orders.csv` | `staging.orders` |
| `order_items.csv` | `staging.order_items` |
| `products.csv` | `staging.products` |

## Target schema

PostgreSQL `traindb`:
- **`staging`** — landing zone for the three raw tables (overwritten/appended each run).
- **`serving`** — exposes one view for business users:
  - **`serving.v_product_status_track`** — joins the three staging tables so each row carries the order, the order line, and the product details.

## Tasks

### 1. Prepare PostgreSQL
- Create database `traindb`, user `train` (password `Ankara06`), grant on the database + the `public` schema.
- Register a `postgresql_conn` Airflow connection pointing at `traindb`.

### 2. Build the DAG
Create `airflow_hw1_dag.py` with these tasks (in order):
1. `CREATE SCHEMA IF NOT EXISTS staging`
2. Load `orders.csv` → `staging.orders`
3. Load `order_items.csv` → `staging.order_items`
4. Load `products.csv` → `staging.products`
5. `CREATE SCHEMA IF NOT EXISTS serving`
6. `CREATE OR REPLACE VIEW serving.v_product_status_track` joining the three staging tables on their FK relationships.

DAG settings:
- `schedule_interval='@hourly'`
- `catchup=False`

### 3. Verify
- Trigger the DAG, confirm all 6 tasks turn green.
- From `psql` (or any client) run `SELECT COUNT(*) FROM serving.v_product_status_track;` and a sample `SELECT * … LIMIT 5;` to confirm the view returns joined rows.

## Deliverables

A single Markdown file `airflow_homework1_solution.md` containing, in order:

1. The exact `psql` commands you ran to create the database, user, and grants.
2. A screenshot or one-line description of the Airflow `postgresql_conn` configuration.
3. The full source of `airflow_hw1_dag.py`.
4. A screenshot of the DAG graph view showing all 6 tasks succeeded.
5. The output of `SELECT COUNT(*) FROM serving.v_product_status_track;` and the first 5 rows of `SELECT * FROM serving.v_product_status_track LIMIT 5;`.

## Grading checklist
- [ ] `traindb` database, `train` user, and grants are in place.
- [ ] `postgresql_conn` Airflow connection works.
- [ ] DAG has 6 tasks with the dependency chain `t1 → t2 → t3 → t4 → t5 → t6`.
- [ ] All three CSVs land in `staging` as tables of the same name.
- [ ] `serving.v_product_status_track` exists and returns non-empty joined rows.
- [ ] DAG `schedule_interval='@hourly'` and `catchup=False`.
- [ ] DAG ran successfully end-to-end at least once (graph view all green).