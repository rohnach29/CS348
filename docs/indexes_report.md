# Indexes Report for Running Tracker Application

## 1. Runner User Index
- **Index Name**: `idx_runner_user`
- **Fields**: `user` (Runner model)
- **Benefited Queries**:
  - `run_list` view: `SELECT ... FROM runs_run r JOIN runs_runner rr ON r.runner_id = rr.id WHERE rr.user_id = %s`
  - `create_run` view: `Runner.objects.get(user=request.user)`
- **Justification**: This index significantly improves the performance of user authentication and run listing, which are core operations in the application. The runner-user relationship is queried frequently for access control and data filtering.

## 2. Run Date-Time Index
- **Index Name**: `idx_run_runner_date_time`
- **Fields**: `runner`, `date`, `start_time` (Run model)
- **Benefited Queries**:
  - `run_list` view: `ORDER BY r.date DESC, r.start_time DESC`
  - `run_report` view: Date-based filtering
- **Justification**: This composite index optimizes the sorting and filtering of runs by date and time, which is crucial for the main run listing and reporting features. It helps maintain performance as the number of runs grows.

## 3. Route Creator-Name Index
- **Index Name**: `idx_route_creator_name`
- **Fields**: `creator`, `name` (Route model)
- **Benefited Queries**:
  - `create_route` view: Duplicate route name checking
  - Route dropdown population in run creation
- **Justification**: This index speeds up the duplicate route name checking process and improves the performance of route selection in the run creation form. It's essential for maintaining data integrity and user experience.

## 4. Run Date Statistics Index
- **Index Name**: `idx_run_runner_date`
- **Fields**: `runner`, `date` (Run model)
- **Benefited Queries**:
  - `run_report` view: Monthly statistics calculation
  - Date-based filtering in reports
- **Justification**: This index optimizes the calculation of monthly statistics and date-based filtering in reports, which are computationally intensive operations that benefit from efficient date-based lookups.

## 5. Run Route Statistics Index
- **Index Name**: `idx_run_route_runner`
- **Fields**: `route`, `runner` (Run model)
- **Benefited Queries**:
  - `run_report` view: Route-based statistics
  - Route performance analysis
- **Justification**: This index improves the performance of route-based statistics and analysis, which are important features for tracking running progress and performance across different routes.

## 6. Comment Time-Based Index
- **Index Name**: `idx_comment_run_commenter_time`
- **Fields**: `run`, `commenter`, `created_at` (Comment model)
- **Benefited Queries**:
  - `add_comment` view: Spam prevention check
  - Comment listing in run detail view
- **Justification**: This composite index optimizes the spam prevention mechanism and comment listing, which are important for maintaining content quality and user experience.

## 7. Run Like Operations Index
- **Index Name**: `idx_runlike_run_runner`
- **Fields**: `run`, `runner` (RunLike model)
- **Benefited Queries**:
  - `toggle_like` view: Like status checking and toggling
  - Like count calculation
- **Justification**: This index improves the performance of like operations, which are frequent social interactions in the application. It helps maintain responsive like/unlike functionality even with many users.

## Performance Impact
These indexes are designed to:
1. Optimize the most frequently accessed queries
2. Improve the performance of computationally intensive operations
3. Maintain data integrity through efficient constraint checking
4. Support the application's core features: run tracking, reporting, and social interactions

The indexes are carefully chosen to balance query performance with write overhead, focusing on operations that are critical to the user experience and application functionality. 